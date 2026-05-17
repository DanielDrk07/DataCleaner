"""
Tests unitarios de DataValidator, DiagnosticReport y ColumnReport.
Ejecutar con: pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
from model.data_validator import DataValidator, DiagnosticReport, ColumnReport


@pytest.fixture
def validator():
    return DataValidator()


@pytest.fixture
def df_mixto():
    """DataFrame con nulos, duplicados y cuatro tipos de dato distintos."""
    return pd.DataFrame({
        "nombre":  ["Ana", "Bob", "Ana",  None,   "Carlos"],
        "edad":    [25,    None,  25,     30,     22],
        "ciudad":  ["Bogota", "Medellin", "Bogota", "Cali", "bogota"],
        "salario": [3000.0, 4500.0, 3000.0, None, 2800.0],
        "activo":  [True, False, True, True, False],
    })


# ══ Tipo de retorno ════════════════════════════════════════════════════════════

class TestReturnType:
    def test_retorna_diagnostic_report(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        assert isinstance(report, DiagnosticReport)

    def test_columnas_son_instancias_de_column_report(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        assert all(isinstance(c, ColumnReport) for c in report.columns)

    def test_conteo_de_filas(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        assert report.total_rows == 5

    def test_conteo_de_columnas(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        assert report.total_cols == 5

    def test_numero_de_column_reports_igual_a_columnas(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        assert len(report.columns) == len(df_mixto.columns)


# ══ Detección de nulos ═════════════════════════════════════════════════════════

class TestNullDetection:
    def test_null_count_en_columna_especifica(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        nombre = next(c for c in report.columns if c.name == "nombre")
        assert nombre.null_count == 1

    def test_null_pct_correcto(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        nombre = next(c for c in report.columns if c.name == "nombre")
        assert nombre.null_pct == 20.0

    def test_total_nulls_es_suma_de_columnas(self, validator, df_mixto):
        # nombre:1 + edad:1 + ciudad:0 + salario:1 + activo:0 = 3
        report = validator.analyze(df_mixto)
        assert report.total_nulls == 3

    def test_columna_sin_nulos(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        ciudad = next(c for c in report.columns if c.name == "ciudad")
        assert ciudad.null_count == 0
        assert ciudad.null_pct == 0.0

    def test_columna_100_pct_nula(self, validator):
        df = pd.DataFrame({"todo_nulo": [None, None, None]})
        report = validator.analyze(df)
        assert report.columns[0].null_count == 3
        assert report.columns[0].null_pct == 100.0

    def test_null_pct_redondeado_a_un_decimal(self, validator):
        # 1/3 filas nulas = 33.333... → debe redondearse a 33.3
        df = pd.DataFrame({"col": [1, None, 3]})
        report = validator.analyze(df)
        assert report.columns[0].null_pct == 33.3


# ══ Detección de duplicados ════════════════════════════════════════════════════

class TestDuplicateDetection:
    def test_detecta_filas_duplicadas(self, validator, df_mixto):
        # Filas 0 y 2 son idénticas: Ana / 25 / Bogota / 3000.0 / True
        report = validator.analyze(df_mixto)
        assert report.duplicate_rows == 1

    def test_sin_duplicados_retorna_cero(self, validator):
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        report = validator.analyze(df)
        assert report.duplicate_rows == 0

    def test_has_issues_true_cuando_hay_duplicados(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        assert report.has_issues is True

    def test_has_issues_false_cuando_dataset_limpio(self, validator):
        df = pd.DataFrame({"a": [1, 2, 3]})
        report = validator.analyze(df)
        assert report.has_issues is False

    def test_has_issues_true_solo_por_nulos(self, validator):
        df = pd.DataFrame({"a": [1, None, 3]})
        report = validator.analyze(df)
        assert report.duplicate_rows == 0
        assert report.has_issues is True


# ══ Clasificación de tipos ══════════════════════════════════════════════════════

class TestColumnTypeClassification:
    def test_columna_texto_dtype_object_o_str(self, validator, df_mixto):
        # Python <3.14 reporta "object", Python 3.14+ reporta "str"
        report = validator.analyze(df_mixto)
        nombre = next(c for c in report.columns if c.name == "nombre")
        assert nombre.dtype in ("object", "str")

    def test_columna_entera(self, validator):
        df = pd.DataFrame({"n": [1, 2, 3]})
        report = validator.analyze(df)
        assert "int" in report.columns[0].dtype.lower()

    def test_columna_float(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        salario = next(c for c in report.columns if c.name == "salario")
        assert "float" in salario.dtype.lower()

    def test_columna_bool(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        activo = next(c for c in report.columns if c.name == "activo")
        assert "bool" in activo.dtype.lower()

    def test_columna_datetime(self, validator):
        df = pd.DataFrame({"fecha": pd.to_datetime(["2024-01-01", "2024-06-15"])})
        report = validator.analyze(df)
        assert "datetime" in report.columns[0].dtype.lower()


# ══ Valores de muestra ══════════════════════════════════════════════════════════

class TestSampleValues:
    def test_muestra_maximo_tres_valores(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        for col in report.columns:
            assert len(col.sample_values) <= 3

    def test_muestra_no_contiene_nulos(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        nombre = next(c for c in report.columns if c.name == "nombre")
        assert None not in nombre.sample_values

    def test_unique_count_no_cuenta_nulos(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        nombre = next(c for c in report.columns if c.name == "nombre")
        # Ana, Bob, Carlos → 3 únicos (None no debe contar)
        assert nombre.unique_count == 3

    def test_unique_count_es_case_sensitive(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        ciudad = next(c for c in report.columns if c.name == "ciudad")
        # Bogota, Medellin, Cali, bogota → 4 únicos (B ≠ b)
        assert ciudad.unique_count == 4


# ══ Casos borde ════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_dataframe_vacio_sin_columnas(self, validator):
        df = pd.DataFrame()
        report = validator.analyze(df)
        assert report.total_rows == 0
        assert report.total_cols == 0
        assert report.total_nulls == 0
        assert report.duplicate_rows == 0
        assert report.columns == []

    def test_dataframe_vacio_con_columnas(self, validator):
        df = pd.DataFrame({
            "a": pd.Series([], dtype="float64"),
            "b": pd.Series([], dtype="object"),
        })
        report = validator.analyze(df)
        assert report.total_rows == 0
        assert report.total_cols == 2
        assert report.total_nulls == 0
        # null_pct debe ser 0.0 aunque len(df) == 0 (guarda contra ZeroDivision)
        assert all(c.null_pct == 0.0 for c in report.columns)

    def test_dataframe_una_sola_fila(self, validator):
        df = pd.DataFrame({"x": [42], "y": ["valor"]})
        report = validator.analyze(df)
        assert report.total_rows == 1
        assert report.duplicate_rows == 0
        assert report.has_issues is False

    def test_todas_las_celdas_nulas(self, validator):
        df = pd.DataFrame({"a": [None, None], "b": [None, None]})
        report = validator.analyze(df)
        assert report.total_nulls == 4
        assert report.has_issues is True

    def test_total_nulls_property_es_suma_de_null_counts(self, validator, df_mixto):
        report = validator.analyze(df_mixto)
        suma_manual = sum(c.null_count for c in report.columns)
        assert report.total_nulls == suma_manual
