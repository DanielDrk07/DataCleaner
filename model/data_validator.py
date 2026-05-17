"""
DataValidator
Analiza un DataFrame y retorna un reporte de problemas detectados.
No modifica datos — solo lectura.
"""
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ColumnReport:
    """Reporte de métricas de calidad para una sola columna.

    Attributes:
        name: Nombre de la columna.
        dtype: Tipo de dato reportado por Pandas (``"int64"``, ``"object"``, etc.).
        null_count: Número absoluto de valores nulos (``NaN`` / ``None``).
        null_pct: Porcentaje de nulos sobre el total de filas, redondeado a 1 decimal.
        unique_count: Cantidad de valores únicos excluyendo nulos.
        sample_values: Hasta 3 valores no nulos de muestra.
    """

    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    sample_values: List[Any]


@dataclass
class DiagnosticReport:
    """Reporte de diagnóstico completo de un DataFrame.

    Attributes:
        total_rows: Número total de filas.
        total_cols: Número total de columnas.
        duplicate_rows: Filas completamente duplicadas (sin contar la primera
            ocurrencia).
        columns: Lista de :class:`ColumnReport` con métricas por columna.
    """

    total_rows: int
    total_cols: int
    duplicate_rows: int
    columns: List[ColumnReport] = field(default_factory=list)

    @property
    def total_nulls(self) -> int:
        """Suma de valores nulos en todas las columnas."""
        return sum(c.null_count for c in self.columns)

    @property
    def has_issues(self) -> bool:
        """``True`` si el dataset tiene duplicados o al menos un valor nulo."""
        return self.duplicate_rows > 0 or self.total_nulls > 0


class DataValidator:
    """Genera un DiagnosticReport a partir de un DataFrame."""

    def analyze(self, df: pd.DataFrame) -> DiagnosticReport:
        """Analiza el DataFrame y devuelve un reporte de calidad de datos.

        Recorre cada columna para calcular conteos de nulos, porcentajes,
        valores únicos y muestras representativas. La función es de solo
        lectura: nunca modifica ``df``.

        Args:
            df: DataFrame a analizar. Puede estar vacío.

        Returns:
            :class:`DiagnosticReport` con métricas globales y por columna.
        """
        report = DiagnosticReport(
            total_rows=len(df),
            total_cols=len(df.columns),
            duplicate_rows=int(df.duplicated().sum()),
        )
        for col in df.columns:
            series = df[col]
            null_count = int(series.isna().sum())
            report.columns.append(ColumnReport(
                name=col,
                dtype=str(series.dtype),
                null_count=null_count,
                null_pct=round(null_count / len(df) * 100, 1) if len(df) > 0 else 0.0,
                unique_count=int(series.nunique(dropna=True)),
                sample_values=series.dropna().head(3).tolist(),
            ))
        return report
