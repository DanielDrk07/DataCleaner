import html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from io import BytesIO
from pathlib import Path

from model.cleaning_model import CleaningModel
from model.data_validator import DataValidator

COLOR_DANGER  = "#EF4444"
COLOR_WARN    = "#F97316"
COLOR_SUCCESS = "#10B981"
COLOR_PRIMARY = "#6C63FF"


def _init_state() -> None:
    """Inicializa las claves del session_state con sus valores por defecto."""
    defaults = {
        "model":          CleaningModel(),
        "validator":      DataValidator(),
        "filename":       None,
        "loaded_file_id": None,
        "feedback":       None,
        "ai_result":      None,
        "ai_for_file":    None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Helpers de sesión ──────────────────────────────────────────────────────────

def get_df() -> pd.DataFrame | None:
    return st.session_state.model.df


def has_data() -> bool:
    df = get_df()
    return df is not None and not df.empty


def set_ok(msg: str) -> None:
    st.session_state.feedback = (msg, "success")


def set_warn(msg: str) -> None:
    st.session_state.feedback = (msg, "warning")


def set_err(msg: str) -> None:
    st.session_state.feedback = (msg, "error")


def health_score(report) -> int:
    """Score de salud del dataset de 0 a 100 (nulos 70 %, duplicados 30 %)."""
    total_cells = report.total_rows * report.total_cols
    null_ratio = report.total_nulls / total_cells if total_cells > 0 else 0
    dup_ratio  = report.duplicate_rows / report.total_rows if report.total_rows > 0 else 0
    return max(0, round(100 - (null_ratio * 70 + dup_ratio * 30)))


def empty_state(icon: str, title: str, subtitle: str = "") -> str:
    """HTML para un estado vacío centrado con ícono y título."""
    sub = f'<p style="font-size:0.82rem;color:#6B7280;margin:0">{subtitle}</p>' if subtitle else ""
    return (
        f'<div style="text-align:center;padding:48px 20px">'
        f'<div style="font-size:2.5rem;margin-bottom:12px">{icon}</div>'
        f'<p style="font-size:1rem;color:#374151;margin:0 0 4px">{title}</p>{sub}</div>'
    )


def simplify_dtype(dtype: str) -> str:
    if "int"      in dtype: return "int"
    if "float"    in dtype: return "float"
    if "object"   in dtype: return "text"
    if dtype      == "str": return "text"
    if "datetime" in dtype: return "date"
    if "bool"     in dtype: return "bool"
    return dtype


def load_uploaded_file(uploaded_file) -> tuple[pd.DataFrame, str]:
    """Lee un archivo subido y retorna (DataFrame, nombre).

    Para CSV prueba 12 combinaciones de encoding/separador automáticamente.
    """
    name    = uploaded_file.name
    ext     = Path(name).suffix.lower()
    content = uploaded_file.read()

    if ext == ".csv":
        for enc in ["utf-8", "latin-1", "cp1252"]:
            for sep in [",", ";", "\t", "|"]:
                try:
                    df = pd.read_csv(BytesIO(content), sep=sep, encoding=enc)
                    if len(df.columns) > 1 and len(df) > 0:
                        return df, name
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue
        try:
            return pd.read_csv(BytesIO(content), encoding="latin-1"), name
        except Exception as e:
            raise ValueError(f"No se pudo leer el CSV: {e}") from e

    if ext == ".xlsx":
        return pd.read_excel(BytesIO(content), engine="openpyxl"), name
    if ext == ".xls":
        return pd.read_excel(BytesIO(content), engine="xlrd"), name

    raise ValueError(f"Formato no soportado: '{ext}'. Usa CSV o Excel.")


# ── Funciones cacheadas ────────────────────────────────────────────────────────

@st.cache_data
def cached_analyze(df: pd.DataFrame):
    return DataValidator().analyze(df)


@st.cache_data
def df_as_str(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(str)


@st.cache_data
def cached_numeric_stats(df: pd.DataFrame) -> list[dict]:
    rows = []
    for col in df.select_dtypes("number").columns:
        s          = df[col].dropna()
        mean_val   = float(s.mean())
        median_val = float(s.median())
        std_val    = float(s.std()) if len(s) > 1 else 0.0
        if std_val and abs(mean_val - median_val) / std_val > 0.2:
            status = "↑ Sesgada +" if mean_val > median_val else "↓ Sesgada −"
        else:
            status = "≈ Simétrica"
        rows.append({
            "Columna":      col,
            "Media":        round(mean_val, 4),
            "Mediana":      round(median_val, 4),
            "Desv. Est.":   round(std_val, 4),
            "Distribución": status,
        })
    return rows


@st.cache_data
def cached_correlation(df: pd.DataFrame, cols: tuple) -> pd.DataFrame:
    """cols debe ser tuple (no list) para que Streamlit pueda cachear."""
    return df[list(cols)].corr(method="pearson")


@st.cache_data
def cached_describe(df: pd.DataFrame) -> pd.DataFrame | None:
    numeric = df.select_dtypes("number")
    if numeric.empty:
        return None
    return numeric.describe().round(2).rename(index={
        "count": "conteo",
        "mean":  "media",
        "std":   "desv. est.",
        "min":   "mínimo",
        "25%":   "percentil 25%",
        "50%":   "percentil 50%",
        "75%":   "percentil 75%",
        "max":   "máximo",
    })


@st.cache_data
def cached_histogram(df: pd.DataFrame, col: str, nbins: int) -> go.Figure:
    fig = px.histogram(
        df, x=col, nbins=nbins,
        title=f"Distribución de {col}",
        color_discrete_sequence=[COLOR_PRIMARY],
    )
    fig.update_layout(
        height=380,
        margin=dict(t=50, b=20, l=20, r=20),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(tickfont=dict(color="#374151"), title=col, showgrid=False),
        yaxis=dict(tickfont=dict(color="#374151"), title="Frecuencia",
                   showgrid=True, gridcolor="#E5E7EB"),
        bargap=0.05,
    )
    return fig


@st.cache_data
def cached_violin(df: pd.DataFrame, col: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Violin(
        y=df[col].dropna(),
        box_visible=True,
        line_color=COLOR_PRIMARY,
        fillcolor="#EEF2FF",
        opacity=0.7,
        meanline_visible=True,
        points="outliers",
        name=col,
        marker=dict(color=COLOR_DANGER, size=4, opacity=0.6),
    ))
    fig.update_layout(
        title=f"Distribución y outliers — {col}",
        height=420,
        margin=dict(t=50, b=20, l=20, r=20),
        paper_bgcolor="white", plot_bgcolor="white",
        yaxis=dict(tickfont=dict(color="#374151"), showgrid=True, gridcolor="#E5E7EB"),
        showlegend=False,
    )
    return fig


@st.cache_data
def cached_category_chart(df: pd.DataFrame, col: str) -> go.Figure:
    counts = (
        df[col].astype(str).value_counts().head(10)
               .reset_index()
    )
    counts.columns = ["Valor", "Frecuencia"]
    counts = counts.sort_values("Frecuencia", ascending=True)

    fig = px.bar(
        counts, x="Frecuencia", y="Valor", orientation="h",
        title=f"Top 10 valores más frecuentes — {col}",
        color="Frecuencia",
        color_continuous_scale=["#EEF2FF", COLOR_PRIMARY],
        text="Frecuencia",
    )
    fig.update_traces(textposition="outside", textfont=dict(color="#374151", size=11))
    fig.update_layout(
        height=max(260, len(counts) * 40 + 90),
        margin=dict(t=50, b=20, l=10, r=60),
        paper_bgcolor="white", plot_bgcolor="white",
        coloraxis_showscale=False,
        xaxis=dict(tickfont=dict(color="#374151"), title="Frecuencia",
                   showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(tickfont=dict(color="#374151"), title=None),
    )
    return fig
