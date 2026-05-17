"""
Pruebas unitarias del CleaningModel.
Ejecutar con: pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
from model.cleaning_model import CleaningModel


@pytest.fixture
def model_with_data():
    """Fixture: modelo con un DataFrame de prueba cargado."""
    m = CleaningModel()
    df = pd.DataFrame({
        "nombre": ["Ana", "Bob", "Ana", None, "  Carlos  "],
        "edad": [25, None, 25, 30, 22],
        "ciudad": ["Bogota", "Medellin", "Bogota", "Cali", "bogota"],
        "salario": [3000.0, 4500.0, 3000.0, None, 2800.0],
    })
    m.load(df)
    return m


class TestLoad:
    def test_carga_dataframe(self, model_with_data):
        assert model_with_data.is_loaded
        assert len(model_with_data.df) == 5

    def test_carga_limpia_historial(self):
        m = CleaningModel()
        df1 = pd.DataFrame({"a": [1, 2]})
        m.load(df1)
        m.drop_duplicates()
        df2 = pd.DataFrame({"b": [3, 4]})
        m.load(df2)
        assert not m.can_undo()


class TestDropNulls:
    def test_elimina_filas_con_nulos_en_columna(self, model_with_data):
        antes = len(model_with_data.df)
        eliminadas = model_with_data.drop_nulls("nombre")
        assert eliminadas == 1
        assert len(model_with_data.df) == antes - 1
        assert model_with_data.df["nombre"].isna().sum() == 0

    def test_elimina_todas_filas_con_nulos(self, model_with_data):
        eliminadas = model_with_data.drop_nulls()
        assert eliminadas > 0
        assert model_with_data.df.isna().sum().sum() == 0


class TestFillNulls:
    def test_rellena_con_media(self, model_with_data):
        media = model_with_data.df["edad"].mean()
        n = model_with_data.fill_nulls("edad", "mean")
        assert n == 1
        assert model_with_data.df["edad"].isna().sum() == 0

    def test_rellena_con_valor_personalizado(self, model_with_data):
        n = model_with_data.fill_nulls("nombre", "personalizado", "Sin nombre")
        assert n == 1
        assert "Sin nombre" in model_with_data.df["nombre"].values

    def test_retorna_cero_si_no_hay_nulos(self, model_with_data):
        n = model_with_data.fill_nulls("ciudad", "mean")
        assert n == 0


class TestDropDuplicates:
    def test_elimina_duplicados(self, model_with_data):
        antes = len(model_with_data.df)
        eliminadas = model_with_data.drop_duplicates()
        assert eliminadas >= 1
        assert len(model_with_data.df) < antes


class TestNormalizeText:
    def test_convierte_a_minusculas(self, model_with_data):
        model_with_data.normalize_text("ciudad", lowercase=True)
        assert all(v == v.lower() for v in model_with_data.df["ciudad"])

    def test_elimina_espacios(self, model_with_data):
        model_with_data.normalize_text("nombre", strip=True)
        assert "  Carlos  " not in model_with_data.df["nombre"].values


class TestConvertType:
    def test_convierte_a_float(self, model_with_data):
        ok, msg = model_with_data.convert_type("edad", "float")
        assert ok
        assert str(model_with_data.df["edad"].dtype) == "float64"

    def test_convierte_a_str(self, model_with_data):
        ok, _ = model_with_data.convert_type("salario", "str")
        assert ok
        assert str(model_with_data.df["salario"].dtype) in ("object", "str", "string")


class TestRenameColumn:
    def test_renombra_correctamente(self, model_with_data):
        ok, msg = model_with_data.rename_column("nombre", "name")
        assert ok
        assert "name" in model_with_data.df.columns
        assert "nombre" not in model_with_data.df.columns

    def test_falla_si_nombre_ya_existe(self, model_with_data):
        ok, _ = model_with_data.rename_column("nombre", "edad")
        assert not ok


class TestFilterRows:
    def test_elimina_filas_por_igualdad_texto(self, model_with_data):
        antes = len(model_with_data.df)
        model_with_data.filter_rows("ciudad", "==", "Bogota")
        assert len(model_with_data.df) < antes

    def test_elimina_filas_por_valor_numerico(self, model_with_data):
        antes = len(model_with_data.df)
        model_with_data.filter_rows("edad", ">", "24")
        assert len(model_with_data.df) < antes

    def test_igualdad_numerica_coerce(self, model_with_data):
        # Verifica que "30" matchea el entero 30 en columna numérica
        antes = len(model_with_data.df)
        model_with_data.filter_rows("edad", "==", "30")
        assert len(model_with_data.df) < antes

    def test_operador_invalido_lanza_error(self, model_with_data):
        with pytest.raises(ValueError):
            model_with_data.filter_rows("salario", ">", "no_es_numero")


class TestDropColumn:
    def test_elimina_columna(self, model_with_data):
        model_with_data.drop_column("ciudad")
        assert "ciudad" not in model_with_data.df.columns

    def test_drop_column_es_deshacible(self, model_with_data):
        model_with_data.drop_column("ciudad")
        model_with_data.undo()
        assert "ciudad" in model_with_data.df.columns


class TestRemoveOutliersIQR:
    def test_elimina_outliers_numericos(self, model_with_data):
        n = model_with_data.remove_outliers_iqr("salario", factor=0.5)
        assert isinstance(n, int)
        assert n >= 0

    def test_falla_en_columna_no_numerica(self, model_with_data):
        with pytest.raises(ValueError):
            model_with_data.remove_outliers_iqr("nombre")

    def test_outliers_es_deshacible(self, model_with_data):
        df_antes = model_with_data.df.copy()
        model_with_data.remove_outliers_iqr("salario", factor=0.5)
        model_with_data.undo()
        pd.testing.assert_frame_equal(model_with_data.df, df_antes)


class TestUndo:
    def test_undo_revierte_operacion(self, model_with_data):
        df_antes = model_with_data.df.copy()
        model_with_data.drop_duplicates()
        model_with_data.undo()
        pd.testing.assert_frame_equal(model_with_data.df, df_antes)

    def test_can_undo_false_cuando_sin_historial(self):
        m = CleaningModel()
        assert not m.can_undo()

    def test_multiples_undos(self, model_with_data):
        model_with_data.drop_duplicates()
        model_with_data.fill_nulls("edad", "mean")
        model_with_data.undo()
        model_with_data.undo()
        assert not model_with_data.can_undo()
