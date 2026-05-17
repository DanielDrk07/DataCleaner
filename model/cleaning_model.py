"""
CleaningModel
Nucleo de logica de limpieza. Usa Pandas internamente.
Mantiene historial de estados para soportar undo.
Completamente independiente de la GUI.
"""
import pandas as pd
from typing import Optional, List, Tuple


class CleaningModel:
    """Motor de limpieza de datos con soporte de historial (undo).

    Encapsula un DataFrame de Pandas y expone operaciones de limpieza
    de alto nivel. Cada operación guarda el estado anterior para permitir
    revertirla con ``undo()``.

    Attributes:
        MAX_HISTORY: Número máximo de estados guardados en el historial.
    """

    MAX_HISTORY = 20

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._history: List[pd.DataFrame] = []
        self._change_log: List[str] = []

    # ── Acceso ─────────────────────────────────────────────────────────

    @property
    def df(self) -> Optional[pd.DataFrame]:
        """DataFrame activo, o ``None`` si no se ha cargado ningún archivo."""
        return self._df

    @property
    def is_loaded(self) -> bool:
        """``True`` si hay un DataFrame cargado."""
        return self._df is not None

    @property
    def change_log(self) -> List[str]:
        """Copia de la lista de descripciones de operaciones aplicadas."""
        return list(self._change_log)

    def load(self, df: pd.DataFrame) -> None:
        """Carga un nuevo DataFrame y reinicia el historial.

        Args:
            df: DataFrame a cargar. Se hace una copia interna para evitar
                mutaciones externas.
        """
        self._df = df.copy()
        self._history.clear()
        self._change_log.clear()

    # ── Historial / Undo ────────────────────────────────────────────────

    def _save_state(self, description: str) -> None:
        """Guarda el estado actual antes de aplicar una operación.

        Si el historial alcanza ``MAX_HISTORY``, descarta el estado más
        antiguo (FIFO).

        Args:
            description: Texto legible que describe la operación a punto de
                aplicarse, usado luego en el log y en el mensaje de undo.
        """
        if self._df is not None:
            self._history.append(self._df.copy())
            if len(self._history) > self.MAX_HISTORY:
                self._history.pop(0)
            self._change_log.append(description)

    def can_undo(self) -> bool:
        """Indica si hay al menos un estado al que se puede revertir."""
        return len(self._history) > 0

    def undo(self) -> str:
        """Revierte la última operación aplicada.

        Returns:
            Descripción de la operación revertida, o cadena vacía si el
            historial estaba vacío.
        """
        if not self.can_undo():
            return ""
        self._df = self._history.pop()
        return self._change_log.pop() if self._change_log else "operacion"

    # ── Operaciones de limpieza ─────────────────────────────────────────

    def drop_nulls(self, column: Optional[str] = None) -> int:
        """Elimina filas que contienen valores nulos.

        Args:
            column: Nombre de la columna a revisar. Si es ``None``, elimina
                cualquier fila que tenga al menos un nulo en cualquier columna.

        Returns:
            Número de filas eliminadas.
        """
        self._require_df()
        before = len(self._df)
        desc = f"Eliminar nulos en '{column}'" if column else "Eliminar filas con nulos"
        self._save_state(desc)
        if column:
            self._df = self._df.dropna(subset=[column]).reset_index(drop=True)
        else:
            self._df = self._df.dropna().reset_index(drop=True)
        return before - len(self._df)

    def fill_nulls(self, column: str, strategy: str, custom_value=None) -> int:
        """Rellena los valores nulos de una columna con la estrategia indicada.

        Args:
            column: Columna objetivo.
            strategy: ``"mean"`` / ``"media"``, ``"median"`` / ``"mediana"``,
                ``"mode"`` / ``"moda"``, o ``"personalizado"`` para usar
                ``custom_value``.
            custom_value: Valor literal con el que rellenar cuando
                ``strategy == "personalizado"``. Se convierte al tipo de la
                columna automáticamente.

        Returns:
            Número de celdas rellenadas (0 si la columna no tenía nulos).

        Raises:
            ValueError: Si ``custom_value`` no puede convertirse al tipo de
                la columna.
        """
        self._require_df()
        null_count = int(self._df[column].isna().sum())
        if null_count == 0:
            return 0
        self._save_state(f"Rellenar nulos en '{column}' [{strategy}]")
        if strategy in ("mean", "media"):
            value = self._df[column].mean()
        elif strategy in ("median", "mediana"):
            value = self._df[column].median()
        elif strategy in ("mode", "moda"):
            mode = self._df[column].mode()
            value = mode[0] if not mode.empty else None
        else:
            value = custom_value
        if value is not None:
            if value == custom_value and custom_value is not None:
                col_dtype = self._df[column].dtype
                try:
                    if pd.api.types.is_numeric_dtype(col_dtype):
                        value = float(custom_value)
                    elif pd.api.types.is_datetime64_any_dtype(col_dtype):
                        value = pd.to_datetime(custom_value)
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"'{custom_value}' no es compatible con el tipo {col_dtype} de '{column}'"
                    ) from e
            self._df[column] = self._df[column].fillna(value)
        return null_count

    def drop_duplicates(self, subset: Optional[List[str]] = None) -> int:
        """Elimina filas duplicadas del DataFrame.

        Args:
            subset: Lista de columnas a considerar para detectar duplicados.
                Si es ``None``, usa todas las columnas.

        Returns:
            Número de filas eliminadas.
        """
        self._require_df()
        before = len(self._df)
        desc = f"Eliminar duplicados {subset}" if subset else "Eliminar filas duplicadas"
        self._save_state(desc)
        self._df = self._df.drop_duplicates(subset=subset).reset_index(drop=True)
        return before - len(self._df)

    def normalize_text(self, column: str, lowercase: bool = True,
                       strip: bool = True, remove_extra_spaces: bool = True) -> int:
        """Normaliza el contenido textual de una columna.

        Args:
            column: Columna de texto a procesar.
            lowercase: Si ``True``, convierte a minúsculas.
            strip: Si ``True``, elimina espacios al inicio y al final.
            remove_extra_spaces: Si ``True``, colapsa múltiples espacios
                internos en uno solo.

        Returns:
            Número de celdas cuyo valor cambió tras la normalización.
        """
        self._require_df()
        original = self._df[column].astype(str).copy()
        self._save_state(f"Normalizar texto en '{column}'")
        series = self._df[column].astype(str)
        if strip:
            series = series.str.strip()
        if remove_extra_spaces:
            series = series.str.replace(r"\s+", " ", regex=True)
        if lowercase:
            series = series.str.lower()
        self._df[column] = series
        return int((self._df[column] != original).sum())

    def convert_type(self, column: str, target_type: str) -> Tuple[bool, str]:
        """Convierte el tipo de dato de una columna.

        Admite conversiones con errores silenciosos (``coerce``): los valores
        que no se pueden convertir se transforman en ``NaN``.

        Args:
            column: Columna a convertir.
            target_type: Tipo destino — ``"int"``, ``"float"``,
                ``"str"`` o ``"datetime"``.

        Returns:
            Tupla ``(éxito, mensaje)``. Si la conversión falla, ``éxito`` es
            ``False`` y ``mensaje`` describe el error; el DataFrame no se
            modifica.
        """
        self._require_df()
        backup = self._df.copy()
        try:
            if target_type == "int":
                self._df[column] = pd.to_numeric(self._df[column], errors="coerce").astype("Int64")
            elif target_type == "float":
                self._df[column] = pd.to_numeric(self._df[column], errors="coerce")
            elif target_type == "str":
                self._df[column] = self._df[column].astype(str)
            elif target_type == "datetime":
                self._df[column] = pd.to_datetime(self._df[column], errors="coerce")
            self._save_state(f"Convertir '{column}' a {target_type}")
            return True, f"'{column}' convertida a {target_type}."
        except Exception as e:
            self._df = backup
            return False, str(e)

    def rename_column(self, old_name: str, new_name: str) -> Tuple[bool, str]:
        """Renombra una columna del DataFrame.

        Args:
            old_name: Nombre actual de la columna.
            new_name: Nuevo nombre deseado.

        Returns:
            Tupla ``(éxito, mensaje)``. Falla si ``new_name`` ya existe en el
            DataFrame.
        """
        self._require_df()
        if new_name in self._df.columns:
            return False, f"Ya existe una columna llamada '{new_name}'."
        self._save_state(f"Renombrar '{old_name}' a '{new_name}'")
        self._df = self._df.rename(columns={old_name: new_name})
        return True, f"Columna renombrada a '{new_name}'."

    def filter_rows(self, column: str, operator: str, value) -> int:
        """Elimina filas que cumplan la condición ``column operator value``.

        Args:
            column: Columna sobre la que se evalúa la condición.
            operator: Operador de comparación — ``"=="``, ``"!="``, ``">"``,
                ``"<"``, ``">="``, ``"<="``, ``"contains"``, ``"startswith"``.
            value: Valor de comparación (se convierte al tipo de la columna
                cuando es pertinente).

        Returns:
            Número de filas eliminadas.

        Raises:
            ValueError: Si el operador o el valor no son compatibles con la
                columna (p. ej. comparar texto con ``">"``).
        """
        self._require_df()
        before = len(self._df)
        backup = self._df.copy()
        try:
            col = self._df[column]
            if operator == "==":
                mask = col == self._coerce_value(col, str(value))
            elif operator == "!=":
                mask = col != self._coerce_value(col, str(value))
            elif operator == ">":
                mask = col > float(value)
            elif operator == "<":
                mask = col < float(value)
            elif operator == ">=":
                mask = col >= float(value)
            elif operator == "<=":
                mask = col <= float(value)
            elif operator == "contains":
                mask = col.astype(str).str.contains(str(value), na=False)
            elif operator == "startswith":
                mask = col.astype(str).str.startswith(str(value), na=False)
            else:
                mask = pd.Series([False] * len(self._df))
            self._df = self._df[~mask].reset_index(drop=True)
            self._save_state(f"Filtrar filas: '{column}' {operator} '{value}'")
        except Exception as e:
            self._df = backup
            raise ValueError(str(e)) from e
        return before - len(self._df)

    def remove_outliers_iqr(self, column: str, factor: float = 1.5) -> int:
        """Elimina filas cuyo valor en ``column`` queda fuera del rango IQR.

        El rango válido se define como
        ``[Q1 − factor×IQR, Q3 + factor×IQR]``.

        Args:
            column: Columna numérica a analizar.
            factor: Multiplicador del IQR. ``1.5`` es el estándar de Tukey;
                ``3.0`` solo elimina valores extremos.

        Returns:
            Número de filas eliminadas.

        Raises:
            ValueError: Si la columna no es de tipo numérico.
        """
        self._require_df()
        col = self._df[column]
        if not pd.api.types.is_numeric_dtype(col):
            raise ValueError(f"La columna '{column}' no es numérica.")
        Q1 = col.quantile(0.25)
        Q3 = col.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR
        before = len(self._df)
        self._save_state(f"Eliminar outliers IQR en '{column}' (factor={factor})")
        self._df = self._df[(col >= lower) & (col <= upper)].reset_index(drop=True)
        return before - len(self._df)

    def drop_column(self, column: str) -> None:
        """Elimina una columna del DataFrame.

        Args:
            column: Nombre de la columna a eliminar.
        """
        self._require_df()
        self._save_state(f"Eliminar columna '{column}'")
        self._df = self._df.drop(columns=[column])

    def _coerce_value(self, col: pd.Series, value: str):
        """Convierte value al dtype de col para comparaciones exactas."""
        if pd.api.types.is_numeric_dtype(col):
            try:
                return int(value)
            except (ValueError, TypeError):
                pass
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        if pd.api.types.is_datetime64_any_dtype(col):
            try:
                return pd.to_datetime(value)
            except Exception:
                return value
        return value

    def _require_df(self) -> None:
        """Lanza RuntimeError si no hay DataFrame cargado."""
        if self._df is None:
            raise RuntimeError("No hay ningun archivo cargado.")
