"""
DataCleaner
Tecnología: Streamlit + Plotly
Ejecutar con: streamlit run app.py
"""

import sys
import os
import html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from io import BytesIO
from pathlib import Path

# Carga variables de .env si el archivo existe (requiere python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Sin python-dotenv la app funciona igual; GROQ_API_KEY debe setearse manualmente

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model.cleaning_model import CleaningModel
from model.data_validator import DataValidator
from model.recommender import get_recommendations, get_local_recommendations

COLOR_DANGER  = "#EF4444"
COLOR_WARN    = "#F97316"
COLOR_SUCCESS = "#10B981"
COLOR_PRIMARY = "#6C63FF"

# ─── Configuración de página ───────────────────────────────────────────────────

st.set_page_config(
    page_title="DataCleaner",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS Personalizado ─────────────────────────────────────────────────────────
# NOTA: Se evita colorear `div` genéricamente en el sidebar porque cascadea
# hacia inputs, métricas y gráficos volviéndolos blancos sobre blanco.

st.markdown("""
<style>
/* ── Escala tipográfica ── */
:root {
    --text-xs:   0.75rem;
    --text-sm:   0.82rem;
    --text-base: 0.9rem;
    --text-md:   0.95rem;
}

/* ── Layout general ── */
/* backgroundColor (#F0F2F6) definido en .streamlit/config.toml */
.block-container { padding-top: 1.2rem; padding-bottom: 1rem; max-width: 1200px; }

/* ── Métricas — data-testid estable desde Streamlit 1.18 ── */
div[data-testid="stMetric"] {
    background: white;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border: 1px solid #D1D5DB;
}
div[data-testid="stMetric"] label { color: #374151 !important; font-weight: 600; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #111827 !important; }

/* ── Sidebar: fondo oscuro ── */
/* Selector directo; omitir > div:first-child para mayor robustez entre versiones */
section[data-testid="stSidebar"] { background: #1B1C2A; }

/* Textos markdown en el sidebar */
section[data-testid="stSidebar"] .stMarkdown p  { color: #C8CAD8; }
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 { color: #FFFFFF; }

/* Labels de widgets */
section[data-testid="stSidebar"] label { color: #B8BAC8 !important; }

/* Opciones de radio y checkboxes */
section[data-testid="stSidebar"] div[data-testid="stRadio"] label p,
section[data-testid="stSidebar"] div[role="radiogroup"] label p,
section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label p,
section[data-testid="stSidebar"] div[data-testid="stCheckbox"] span { color: #E8EAF6 !important; }

/* Caption */
section[data-testid="stSidebar"] .stCaption p { color: #9EA3C0 !important; }

/* Separadores */
section[data-testid="stSidebar"] hr { border-color: #2E3050; }

/* Botones del sidebar */
section[data-testid="stSidebar"] .stButton > button {
    background: #6C63FF;
    color: white !important;
    border: none;
    border-radius: 8px;
    width: 100%;
    font-weight: 600;
    transition: background 0.18s;
}
section[data-testid="stSidebar"] .stButton > button:hover  { background: #5A52E0; }
section[data-testid="stSidebar"] .stButton > button:active { background: #4840CC; }

/* Expander del sidebar */
section[data-testid="stSidebar"] details summary p { color: #D0D2E0 !important; }

/* ── Cabecera principal ── */
.app-header {
    background: linear-gradient(135deg, #6C63FF 0%, #4ECDC4 100%);
    color: white;
    padding: 22px 28px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(108,99,255,0.22);
}
.app-header h1 { color: white !important; margin: 0 0 4px 0; font-size: 1.7rem; }
.app-header p  { color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem; }

/* ── Tarjetas de columna ── */
.col-card {
    background: white;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    border-left: 4px solid #D1D5DB;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.col-card.danger  { border-left-color: #EF4444; }
.col-card.warning { border-left-color: #F97316; }
.col-card.good    { border-left-color: #10B981; }

/* ── Badge de tipo ── */
.type-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: var(--text-xs);
    font-weight: 700;
    background: #EEF2FF;
    color: #4F46E5;
    letter-spacing: 0.02em;
    border: 1px solid #C7D2FE;
}

/* ── Tarjeta de recomendación local ── */
.rec-local {
    background: #EEF2FF;
    border-left: 3px solid #6C63FF;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: var(--text-base);
    color: #1E1B4B;
}

/* ── Bloque de respuesta IA ── */
.rec-ai {
    background: linear-gradient(135deg, #EDE9FE 0%, #D1FAF5 100%);
    border: 1px solid #A5B4FC;
    border-radius: 12px;
    padding: 16px 20px;
    font-size: var(--text-base);
    color: #1E293B;
    line-height: 1.6;
    white-space: pre-wrap;
}

/* ── Log de operaciones ── */
.log-entry {
    padding: 7px 14px;
    border-radius: 6px;
    margin: 5px 0;
    background: #EEF2FF;
    border-left: 3px solid #6C63FF;
    font-size: var(--text-sm);
    color: #1E1B4B;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: white;
    border-radius: 12px;
    padding: 5px;
    border: 1px solid #D1D5DB;
    margin-bottom: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 600;
    color: #374151 !important;
}
.stTabs [aria-selected="true"] {
    background: #EEF2FF !important;
    color: #4F46E5 !important;
}

/* ── Captions en área principal ── */
.main .stCaption p { color: #4B5563 !important; }

/* ── Headings en área principal ── */
.main h4 { color: #111827; }

@media (max-width: 768px) {
    div[data-testid="stMetric"] { padding: 10px 12px; }
    .app-header h1 { font-size: 1.3rem; }
    .app-header p  { font-size: 0.8rem; }
    .block-container { padding-top: 0.8rem; }
}
</style>
""", unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────────

def _init_state():
    """Inicializa las claves del session_state con sus valores por defecto.

    Solo asigna las claves que aún no existen para no sobreescribir el
    estado en recargas parciales de Streamlit.
    """
    defaults = {
        "model": CleaningModel(),
        "validator": DataValidator(),
        "filename": None,
        "loaded_file_id": None,
        "feedback": None,       # (msg, kind) | None
        "ai_result": None,      # str con respuesta Groq | None
        "ai_for_file": None,    # filename al momento de pedir IA
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ─── Utilidades ────────────────────────────────────────────────────────────────

@st.cache_data
def _cached_analyze(df: pd.DataFrame):
    """Analiza el DataFrame y retorna un DiagnosticReport (cacheado por Streamlit)."""
    return DataValidator().analyze(df)


@st.cache_data
def _df_as_str(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte todas las columnas a str para búsquedas de texto (cacheado)."""
    return df.astype(str)


@st.cache_data
def _cached_numeric_stats(df: pd.DataFrame) -> list[dict]:
    """Calcula media, mediana, desv. estándar y sesgo para columnas numéricas.

    Returns:
        Lista de dicts con claves ``Columna``, ``Media``, ``Mediana``,
        ``Desv. Est.`` y ``Distribución``.
    """
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
def _cached_correlation(df: pd.DataFrame, cols: tuple) -> pd.DataFrame:
    """Calcula la matriz de correlación de Pearson para las columnas indicadas.

    Args:
        cols: Tupla (no lista) para que Streamlit pueda cachear el resultado.
    """
    return df[list(cols)].corr(method="pearson")


@st.cache_data
def _cached_describe(df: pd.DataFrame) -> pd.DataFrame | None:
    """Retorna estadísticas descriptivas de columnas numéricas en español.

    Returns:
        DataFrame con índices traducidos al español, o ``None`` si no hay
        columnas numéricas.
    """
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
def _cached_histogram(df: pd.DataFrame, col: str, nbins: int) -> go.Figure:
    """Genera un histograma de Plotly para la columna numérica indicada."""
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
def _cached_violin(df: pd.DataFrame, col: str) -> go.Figure:
    """Genera un violin plot con box plot y puntos de outliers superpuestos."""
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
def _cached_category_chart(df: pd.DataFrame, col: str) -> go.Figure:
    """Genera un bar chart horizontal con los 10 valores más frecuentes de una columna categórica."""
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


def get_df() -> pd.DataFrame | None:
    """Retorna el DataFrame activo desde el session_state, o ``None``."""
    return st.session_state.model.df


def has_data() -> bool:
    """``True`` si hay un DataFrame no vacío cargado en la sesión."""
    df = get_df()
    return df is not None and not df.empty


def set_ok(msg: str):   st.session_state.feedback = (msg, "success")
def set_warn(msg: str): st.session_state.feedback = (msg, "warning")
def set_err(msg: str):  st.session_state.feedback = (msg, "error")


def health_score(report) -> int:
    """Calcula un puntaje de salud del dataset de 0 a 100.

    La fórmula penaliza los nulos (peso 70 %) y los duplicados (peso 30 %),
    usando sus proporciones respecto al total de celdas y filas.

    Args:
        report: DiagnosticReport del dataset.

    Returns:
        Entero entre 0 (muy sucio) y 100 (sin problemas).
    """
    total_cells = report.total_rows * report.total_cols
    null_ratio = report.total_nulls / total_cells if total_cells > 0 else 0
    dup_ratio  = report.duplicate_rows / report.total_rows if report.total_rows > 0 else 0
    return max(0, round(100 - (null_ratio * 70 + dup_ratio * 30)))


def _empty_state(icon: str, title: str, subtitle: str = "") -> str:
    """Genera HTML para un estado vacío centrado con ícono, título y subtítulo opcional.

    Args:
        icon: Emoji o carácter a mostrar como ícono grande.
        title: Texto principal del estado vacío.
        subtitle: Texto secundario de ayuda (opcional).

    Returns:
        Cadena HTML lista para pasar a ``st.markdown(..., unsafe_allow_html=True)``.
    """
    sub = f'<p style="font-size:0.82rem;color:#6B7280;margin:0">{subtitle}</p>' if subtitle else ""
    return (f'<div style="text-align:center;padding:48px 20px">'
            f'<div style="font-size:2.5rem;margin-bottom:12px">{icon}</div>'
            f'<p style="font-size:1rem;color:#374151;margin:0 0 4px">{title}</p>{sub}</div>')


def simplify_dtype(dtype: str) -> str:
    """Convierte un dtype de Pandas a una etiqueta legible para la UI.

    Args:
        dtype: String del dtype (p. ej. ``"int64"``, ``"float32"``).

    Returns:
        Etiqueta corta: ``"int"``, ``"float"``, ``"text"``, ``"date"``,
        ``"bool"``, o el dtype original si no hay coincidencia.
    """
    if "int"      in dtype: return "int"
    if "float"    in dtype: return "float"
    if "object"   in dtype: return "text"
    if dtype      == "str": return "text"
    if "datetime" in dtype: return "date"
    if "bool"     in dtype: return "bool"
    return dtype


def load_uploaded_file(uploaded_file) -> tuple[pd.DataFrame, str]:
    """Lee un archivo subido por el usuario y retorna un DataFrame.

    Para CSV prueba combinaciones de codificación (utf-8, latin-1, cp1252)
    y separador (',', ';', '\\t', '|') hasta encontrar una que produzca
    más de una columna. Para Excel usa el engine apropiado según la extensión.

    Args:
        uploaded_file: Objeto ``UploadedFile`` de Streamlit.

    Returns:
        Tupla ``(DataFrame, nombre_del_archivo)``.

    Raises:
        ValueError: Si el formato no es soportado o no se puede leer el CSV.
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

    elif ext == ".xlsx":
        return pd.read_excel(BytesIO(content), engine="openpyxl"), name
    elif ext == ".xls":
        return pd.read_excel(BytesIO(content), engine="xlrd"), name

    raise ValueError(f"Formato no soportado: '{ext}'. Usa CSV o Excel.")


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ✨ DataCleaner")
    st.caption("v2.0")
    st.markdown("---")

    # ── Carga de archivo ──────────────────────────────────────────────────────
    st.markdown("### 📂 Cargar Archivo")
    uploaded = st.file_uploader(
        "CSV o Excel",
        type=["csv", "xlsx", "xls"],
        label_visibility="hidden",
    )

    if uploaded:
        file_id = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.loaded_file_id != file_id:
            try:
                df_loaded, fname = load_uploaded_file(uploaded)
                st.session_state.model.load(df_loaded)
                st.session_state.filename     = fname
                st.session_state.loaded_file_id = file_id
                st.session_state.ai_result    = None  # resetear IA al cargar nuevo archivo
                set_ok(f"✅ **{fname}** cargado — {len(df_loaded):,} filas × {len(df_loaded.columns)} columnas")
                st.rerun()
            except Exception as exc:
                set_err(f"❌ Error al cargar: {exc}")

    if not has_data():
        st.markdown(_empty_state("☝", "Carga un archivo para comenzar"),
                    unsafe_allow_html=True)
        st.stop()

    # ── Info del archivo
    df_current = get_df()
    st.markdown(f"""
    <div style="background:#252639;padding:10px 14px;border-radius:8px;
                font-size:0.82rem;border:1px solid #3A3C54;">
        <b style="color:#A8AACC">📄 {html.escape(st.session_state.filename)}</b><br>
        <span style="color:#6C63FF;font-weight:600">{len(df_current):,}</span>
        <span style="color:#9EA3C0"> filas &nbsp;·&nbsp; </span>
        <span style="color:#6C63FF;font-weight:600">{len(df_current.columns)}</span>
        <span style="color:#9EA3C0"> columnas</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")

    # ── Deshacer
    if st.button("↩  Deshacer última operación",
                 disabled=not st.session_state.model.can_undo(),
                 use_container_width=True):
        op = st.session_state.model.undo()
        set_ok(f"↩ Deshecho: **{op}**")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🛠 Operaciones")

    cols = list(get_df().columns)

    # 1 ── Tratar Nulos ────────────────────────────────────────────────────────
    with st.expander("🔸 Tratar Nulos"):
        col_options = ["— todas las columnas —"] + cols
        null_col = st.selectbox("Columna", col_options, key="null_col")
        action   = st.radio("Acción", ["Eliminar filas con nulos", "Rellenar nulos"],
                            key="null_act", horizontal=False)

        if action == "Rellenar nulos":
            strat = st.selectbox("Estrategia", ["media", "mediana", "moda", "personalizado"],
                                 key="null_strat")
            custom_val = st.text_input("Valor personalizado", key="null_custom") \
                         if strat == "personalizado" else ""
            if st.button("Rellenar", key="btn_fill", use_container_width=True):
                target = None if null_col.startswith("—") else null_col
                if not target:
                    set_warn("Selecciona una columna específica para rellenar")
                else:
                    with st.spinner("Procesando..."):
                        n = st.session_state.model.fill_nulls(target, strat, custom_value=custom_val or None)
                    set_ok(f"✅ {n} valores rellenos en **{target}**")
                st.rerun()
        else:
            st.caption("⚠️ Se eliminarán las filas que tengan nulos.")
            confirm_null = st.checkbox("Confirmar eliminación", key="confirm_null_drop")
            if st.button("Eliminar filas con nulos", key="btn_drop_null",
                         use_container_width=True, disabled=not confirm_null):
                target = None if null_col.startswith("—") else null_col
                with st.spinner("Procesando..."):
                    n = st.session_state.model.drop_nulls(target)
                set_ok(f"✅ {n} filas eliminadas")
                st.rerun()

    # 2 ── Duplicados ──────────────────────────────────────────────────────────
    with st.expander("🔁 Eliminar Duplicados"):
        st.caption("Elimina filas completamente idénticas en todo el dataset.")
        confirm_dup = st.checkbox("Confirmar eliminación", key="confirm_dup")
        if st.button("Eliminar Duplicados", key="btn_dup",
                     use_container_width=True, disabled=not confirm_dup):
            with st.spinner("Procesando..."):
                n = st.session_state.model.drop_duplicates()
            set_ok(f"✅ {n} filas duplicadas eliminadas")
            st.rerun()

    # 3 ── Normalizar texto ────────────────────────────────────────────────────
    with st.expander("🔤 Normalizar Texto"):
        norm_col   = st.selectbox("Columna de texto", cols, key="norm_col")
        norm_lower = st.checkbox("Convertir a minúsculas",          value=True, key="norm_lower")
        norm_strip = st.checkbox("Eliminar espacios inicio/fin",    value=True, key="norm_strip")
        norm_extra = st.checkbox("Eliminar espacios extra internos", value=True, key="norm_extra")
        if st.button("Normalizar", key="btn_norm", use_container_width=True):
            with st.spinner("Normalizando..."):
                n = st.session_state.model.normalize_text(norm_col, norm_lower, norm_strip, norm_extra)
            set_ok(f"✅ {n} celdas normalizadas en **{norm_col}**")
            st.rerun()

    # 4 ── Convertir tipo ──────────────────────────────────────────────────────
    with st.expander("🔄 Convertir Tipo de Dato"):
        type_col    = st.selectbox("Columna", cols, key="type_col")
        type_target = st.selectbox("Convertir a", ["int", "float", "str", "datetime"], key="type_target")
        if st.button("Convertir", key="btn_type", use_container_width=True):
            with st.spinner("Convirtiendo..."):
                ok, msg = st.session_state.model.convert_type(type_col, type_target)
            (set_ok if ok else set_err)(("✅ " if ok else "❌ ") + msg)
            st.rerun()

    # 5 ── Renombrar columna ───────────────────────────────────────────────────
    with st.expander("✏️ Renombrar Columna"):
        rename_old = st.selectbox("Columna a renombrar", cols, key="rename_old")
        rename_new = st.text_input("Nuevo nombre", placeholder="nombre_nuevo", key="rename_new")
        if st.button("Renombrar", key="btn_rename", use_container_width=True):
            if rename_new.strip():
                with st.spinner("Renombrando..."):
                    ok, msg = st.session_state.model.rename_column(rename_old, rename_new.strip())
                (set_ok if ok else set_err)(("✅ " if ok else "❌ ") + msg)
                st.rerun()
            else:
                set_warn("⚠️ Escribe un nombre válido")

    # 6 ── Filtrar / eliminar filas ────────────────────────────────────────────
    with st.expander("🔍 Filtrar / Eliminar Filas"):
        filter_col = st.selectbox("Columna", cols, key="filter_col")
        filter_op  = st.selectbox("Operador",
                                  ["==", "!=", ">", "<", ">=", "<=", "contains", "startswith"],
                                  key="filter_op")
        filter_val = st.text_input("Valor", key="filter_val")
        st.caption("⚠️ Se eliminarán las filas que **cumplan** la condición.")
        confirm_filter = st.checkbox("Confirmar eliminación", key="confirm_filter")
        if st.button("Eliminar filas filtradas", key="btn_filter",
                     use_container_width=True, disabled=not confirm_filter):
            if filter_val.strip():
                try:
                    with st.spinner("Procesando..."):
                        n = st.session_state.model.filter_rows(filter_col, filter_op, filter_val.strip())
                    set_ok(f"✅ {n} filas eliminadas")
                except ValueError as e:
                    set_err(f"❌ {e}")
                st.rerun()
            else:
                set_warn("Escribe un valor para filtrar")

    # 7 ── Eliminar columna ────────────────────────────────────────────────────
    with st.expander("🗑️ Eliminar Columna"):
        del_col = st.selectbox("Columna", cols, key="del_col")
        st.warning(f"Se eliminará permanentemente **{del_col}**. Puedes deshacer después.")
        confirm_del = st.checkbox(f"Confirmo que quiero eliminar '{del_col}'", key="confirm_del_col")
        if st.button(f"⚠️ Eliminar '{del_col}'", key="btn_del_col",
                     use_container_width=True, type="primary", disabled=not confirm_del):
            with st.spinner("Eliminando columna..."):
                st.session_state.model.drop_column(del_col)
            set_ok(f"✅ Columna **{del_col}** eliminada")
            st.rerun()

    # 8 ── Eliminar valores atípicos (IQR) ────────────────────────────────────
    with st.expander("📉 Eliminar Valores Atípicos (IQR)"):
        numeric_cols_sidebar = list(get_df().select_dtypes(include="number").columns)
        if not numeric_cols_sidebar:
            st.caption("No hay columnas numéricas en el dataset.")
        else:
            iqr_col    = st.selectbox("Columna numérica", numeric_cols_sidebar, key="iqr_col")
            iqr_factor = st.number_input("Factor IQR", min_value=0.1, max_value=10.0,
                                         value=1.5, step=0.1, key="iqr_factor")
            st.caption("Elimina filas fuera de Q1 − factor×IQR  y  Q3 + factor×IQR. "
                       "1.5 = estándar · 3.0 = solo extremos.")
            if st.button("Eliminar outliers", key="btn_iqr", use_container_width=True):
                try:
                    with st.spinner("Procesando..."):
                        n = st.session_state.model.remove_outliers_iqr(iqr_col, factor=iqr_factor)
                    set_ok(f"✅ {n} filas con valores atípicos eliminadas en **{iqr_col}**")
                except ValueError as e:
                    set_warn(f"⚠️ {e}")
                st.rerun()

    st.markdown("---")

    # ── Exportar ──────────────────────────────────────────────────────────────
    st.markdown("### 💾 Exportar")
    export_name = st.text_input("Nombre del archivo", value="datos_limpios", key="export_name")

    df_export = get_df()

    buf_csv = BytesIO()
    df_export.to_csv(buf_csv, index=False, encoding="utf-8-sig")
    buf_csv.seek(0)
    st.download_button("⬇ Descargar CSV", data=buf_csv,
                       file_name=f"{export_name}.csv", mime="text/csv",
                       use_container_width=True)

    buf_xlsx = BytesIO()
    df_export.to_excel(buf_xlsx, index=False, engine="openpyxl")
    buf_xlsx.seek(0)
    st.download_button("⬇ Descargar Excel", data=buf_xlsx,
                       file_name=f"{export_name}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)

    if st.session_state.model.change_log:
        log_text = "\n".join(f"{i+1:02d}. {e}"
                             for i, e in enumerate(st.session_state.model.change_log))
        st.download_button("📋 Descargar Log de Cambios", data=log_text.encode("utf-8"),
                           file_name="log_cambios.txt", mime="text/plain",
                           use_container_width=True)

# ─── CONTENIDO PRINCIPAL ───────────────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <h1>✨ DataCleaner</h1>
    <p>Limpia, transforma y exporta tus datos de forma visual e intuitiva · Streamlit + Plotly</p>
</div>
""", unsafe_allow_html=True)

# Feedback
if st.session_state.feedback:
    msg, kind = st.session_state.feedback
    icons = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "ℹ️"}
    st.toast(msg, icon=icons.get(kind, "ℹ️"))
    st.session_state.feedback = None

# ─── Métricas rápidas ──────────────────────────────────────────────────────────

df     = get_df()
report = _cached_analyze(df)
score  = health_score(report)

m1, m2, m3 = st.columns(3)
m4, m5     = st.columns(2)
with m1: st.metric("📋 Filas",    f"{report.total_rows:,}")
with m2: st.metric("📊 Columnas", report.total_cols)
with m3:
    icon = "🟢" if score >= 70 else ("🟡" if score >= 40 else "🔴")
    st.metric(f"{icon} Salud", f"{score}/100")
with m4: st.metric("⚠️ Nulos", f"{report.total_nulls:,}",
                   delta=f"-{report.total_nulls:,}" if report.total_nulls else None,
                   delta_color="inverse")
with m5: st.metric("🔁 Duplicados", f"{report.duplicate_rows:,}",
                   delta=f"-{report.duplicate_rows:,}" if report.duplicate_rows else None,
                   delta_color="inverse")

st.markdown("")

# ─── Tabs ──────────────────────────────────────────────────────────────────────

tab_datos, tab_diag, tab_medias, tab_corr, tab_hist = st.tabs([
    "📊   Vista de Datos",
    "🔍   Diagnóstico & IA",
    "📈   Estadísticas",
    "🔗   Correlaciones",
    "📋   Historial de Cambios",
])

# ══ TAB 1: Vista de Datos ══════════════════════════════════════════════════════

with tab_datos:
    search = st.text_input(
        "Buscar en datos", placeholder="🔎  Filtra filas que contengan cualquier texto...",
        label_visibility="hidden", key="search_data",
    )
    display_df = df
    if search.strip():
        mask = _df_as_str(df).apply(
            lambda c: c.str.contains(search, case=False, na=False, regex=False)
        ).any(axis=1)
        display_df = df[mask]
        st.caption(f"Mostrando **{len(display_df):,}** de **{len(df):,}** filas")

    row_h = 35
    dynamic_height = min(600, max(200, len(display_df) * row_h + 38))
    st.dataframe(display_df, use_container_width=True, height=dynamic_height)
    st.caption("💡 Las operaciones de limpieza están en el **panel izquierdo**. "
               "La tabla se actualiza automáticamente después de cada operación.")

# ══ TAB 2: Diagnóstico & IA ═══════════════════════════════════════════════════

with tab_diag:

    # ── Fila superior: gauge + resumen de problemas ───────────────────────────
    col_gauge, col_issues = st.columns([1, 1], gap="large")

    with col_gauge:
        gauge_color = COLOR_SUCCESS if score >= 70 else (COLOR_WARN if score >= 40 else COLOR_DANGER)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 28, "color": gauge_color}},
            title={"text": "Salud del Dataset", "font": {"size": 14, "color": "#374151"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#CCC"},
                "bar": {"color": gauge_color, "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0,  40], "color": "#FFF0F0"},
                    {"range": [40, 70], "color": "#FFFBF0"},
                    {"range": [70,100], "color": "#F0FFF4"},
                ],
                "threshold": {
                    "line": {"color": gauge_color, "width": 3},
                    "thickness": 0.8, "value": score,
                },
            },
        ))
        fig_gauge.update_layout(height=230, margin=dict(t=30, b=0, l=20, r=20),
                                paper_bgcolor="white")
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_issues:
        st.markdown("#### Resumen de Problemas")
        n_issues = 0
        if report.total_nulls > 0:
            st.warning(f"⚠️ **{report.total_nulls:,} valores nulos** en el dataset")
            n_issues += 1
        if report.duplicate_rows > 0:
            st.warning(f"⚠️ **{report.duplicate_rows:,} filas duplicadas** detectadas")
            n_issues += 1
        critical = [c for c in report.columns if c.null_pct > 50]
        if critical:
            names = ", ".join(f"`{c.name}`" for c in critical)
            st.error(f"🚨 Columnas críticas (>50% nulos): {names}")
            n_issues += 1
        if n_issues == 0:
            st.success("✅ ¡El dataset no tiene problemas detectados! Listo para exportar.")

        # Pie chart de tipos de datos
        type_counts: dict[str, int] = {}
        for c in report.columns:
            t = simplify_dtype(c.dtype)
            type_counts[t] = type_counts.get(t, 0) + 1

        fig_pie = px.pie(
            values=list(type_counts.values()),
            names=list(type_counts.keys()),
            title="Distribución de tipos de datos",
            color_discrete_sequence=["#6C63FF", "#4ECDC4", "#FF6B6B", "#FFD93D", "#A8E6CF"],
            hole=0.45,
        )
        fig_pie.update_layout(height=220, margin=dict(t=35, b=5, l=0, r=0),
                              showlegend=False,
                              paper_bgcolor="white")
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # ── Gráfico de nulos por columna ──────────────────────────────────────────
    col_with_nulls = [c for c in report.columns if c.null_count > 0]
    if col_with_nulls:
        st.markdown("#### Valores Nulos por Columna")
        null_df = pd.DataFrame({
            "Columna": [c.name for c in col_with_nulls],
            "% Nulos": [c.null_pct for c in col_with_nulls],
            "# Nulos": [c.null_count for c in col_with_nulls],
        }).sort_values("% Nulos", ascending=True)

        fig_bar = px.bar(
            null_df, x="% Nulos", y="Columna", orientation="h",
            text="# Nulos", color="% Nulos",
            color_continuous_scale=["#D4EDDA", "#FFF3CD", "#F8D7DA"],
            range_color=[0, 100],
        )
        fig_bar.update_traces(textposition="outside", marker_line_width=0)
        fig_bar.update_layout(
            height=max(180, len(col_with_nulls) * 38 + 60),
            margin=dict(t=10, b=10, l=10, r=40),
            coloraxis_showscale=False,
            xaxis=dict(range=[0, 115], title="% de valores nulos"),
            paper_bgcolor="white", plot_bgcolor="white",
        )
        fig_bar.update_xaxes(showgrid=True, gridcolor="#E5E7EB", tickfont=dict(color="#374151"), title_font=dict(color="#374151"))
        fig_bar.update_yaxes(tickfont=dict(color="#374151"))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.success("✅ Ninguna columna tiene valores nulos")

    st.markdown("---")

    # ── Detalle por columna ───────────────────────────────────────────────────
    st.markdown("#### Detalle por Columna")
    st.markdown('<ul role="list" style="list-style:none;padding:0;margin:0">', unsafe_allow_html=True)
    for col_rep in report.columns:
        css_class   = "danger" if col_rep.null_pct > 50 else ("warning" if col_rep.null_pct > 0 else "good")
        bar_color   = COLOR_DANGER if col_rep.null_pct > 50 else (COLOR_WARN if col_rep.null_pct > 0 else COLOR_SUCCESS)
        dtype_label = simplify_dtype(col_rep.dtype)
        sample_str  = html.escape(", ".join(str(v)[:25] for v in col_rep.sample_values)) \
                      if col_rep.sample_values else "—"
        col_name    = html.escape(col_rep.name)

        st.markdown(f"""
        <li role="listitem" class="col-card {css_class}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <b style="color:#111827;font-size:0.95rem">{col_name}</b>
                    &nbsp;<span class="type-badge">{dtype_label}</span>
                    &nbsp;<span style="color:#6B7280;font-size:0.78rem">{col_rep.unique_count} únicos</span>
                </div>
                <div style="text-align:right;font-size:0.82rem;color:#374151">
                    {col_rep.null_count} nulos
                    <b style="color:{bar_color}"> ({col_rep.null_pct}%)</b>
                </div>
            </div>
            <div style="margin-top:8px;background:#E5E7EB;border-radius:4px;height:6px;overflow:hidden">
                <div style="width:{col_rep.null_pct}%;background:{bar_color};height:6px;border-radius:4px"></div>
            </div>
            <div style="margin-top:5px;color:#6B7280;font-size:0.78rem">
                Muestra: <span style="color:#1F2937">{sample_str}</span>
            </div>
        </li>
        """, unsafe_allow_html=True)
    st.markdown('</ul>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Recomendaciones ───────────────────────────────────────────────────────
    st.markdown("#### 💡 Recomendaciones de Limpieza")

    # Siempre: reglas locales
    local_recs = get_local_recommendations(report)
    st.markdown("**Análisis automático:**")
    for rec in local_recs:
        st.markdown(f'<div class="rec-local">• {html.escape(rec)}</div>', unsafe_allow_html=True)

    st.markdown("")

    # IA: botón para llamar a Groq, resultado cacheado en session_state
    st.markdown("**Recomendaciones con Inteligencia Artificial (Groq · Llama 3):**")

    ai_result = st.session_state.ai_result
    col_btn, col_info = st.columns([1, 2])

    with col_btn:
        ai_clicked = st.button("🤖 Pedir recomendaciones IA", use_container_width=True)

    with col_info:
        st.caption("Usa la API gratuita de Groq. Requiere la variable de entorno `GROQ_API_KEY`.")

    if ai_clicked:
        with st.spinner("Consultando IA..."):
            recs = get_recommendations(report)
            st.session_state.ai_result   = recs["ai"]
            st.session_state.ai_for_file = st.session_state.filename
        st.rerun()

    if ai_result:
        if ai_result.startswith("["):
            st.warning(ai_result)
        else:
            st.markdown(f'<div class="rec-ai">{html.escape(ai_result)}</div>', unsafe_allow_html=True)
            if st.session_state.ai_for_file:
                st.caption(f"Análisis para: {st.session_state.ai_for_file}")

# ══ TAB 3: Estadísticas ═══════════════════════════════════════════════════════

with tab_medias:
    numeric_cols_m     = df.select_dtypes(include="number").columns.tolist()
    categorical_cols_m = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # ── 1. Resumen general ────────────────────────────────────────────────────
    st.markdown("#### 📋 Resumen General")
    desc_df = _cached_describe(df)
    if desc_df is not None:
        def _col_gradient(s: pd.Series) -> list[str]:
            lo, hi = s.min(), s.max()
            out = []
            for v in s:
                if pd.isna(v) or hi == lo:
                    out.append("")
                    continue
                t = (v - lo) / (hi - lo)
                # #EFF6FF → #1E40AF  (light blue → dark blue)
                r = int(239 - t * 209)
                g = int(246 - t * 182)
                b = int(255 - t * 80)
                tc = "#111827" if t < 0.55 else "white"
                out.append(f"background-color: rgb({r},{g},{b}); color: {tc}")
            return out
        st.dataframe(
            desc_df.style.apply(_col_gradient, axis=0).format("{:.2f}"),
            use_container_width=True,
        )
        st.caption("Estadísticas descriptivas de todas las columnas numéricas, redondeadas a 2 decimales.")
    else:
        st.info("No hay columnas numéricas para mostrar el resumen.")

    st.markdown("---")

    # ── 2. Distribuciones ────────────────────────────────────────────────────
    st.markdown("#### 📊 Distribuciones")
    if not numeric_cols_m:
        st.info("No hay columnas numéricas en el dataset.")
    else:
        _col_hist_sel, _col_hist_bins = st.columns([2, 1])
        with _col_hist_sel:
            hist_col = st.selectbox("Columna numérica", numeric_cols_m, key="hist_col")
        with _col_hist_bins:
            hist_bins = st.slider("Barras", min_value=5, max_value=100, value=30, key="hist_bins")
        st.plotly_chart(_cached_histogram(df, hist_col, hist_bins), use_container_width=True)

    st.markdown("---")

    # ── 3. Box plot & violín ──────────────────────────────────────────────────
    st.markdown("#### 📦 Box Plot & Violín")
    if not numeric_cols_m:
        st.info("No hay columnas numéricas en el dataset.")
    else:
        box_col = st.selectbox("Columna numérica", numeric_cols_m, key="box_col")
        st.plotly_chart(_cached_violin(df, box_col), use_container_width=True)
        st.caption("Los puntos fuera de los bigotes son outliers. "
                   "La línea central es la mediana; el rombo es la media.")

    st.markdown("---")

    # ── 4. Frecuencias categóricas ────────────────────────────────────────────
    st.markdown("#### 🏷️ Frecuencias Categóricas")
    if not categorical_cols_m:
        st.info("No hay columnas categóricas (texto u objeto) en el dataset.")
    else:
        cat_col = st.selectbox("Columna categórica", categorical_cols_m, key="cat_col")
        st.plotly_chart(_cached_category_chart(df, cat_col), use_container_width=True)

    st.markdown("---")

    # ── 5. Comparación de medias ──────────────────────────────────────────────
    st.markdown("#### 📈 Comparación de Medias")
    if not numeric_cols_m:
        st.info("No hay columnas numéricas en el dataset.")
    else:
        rows_m  = _cached_numeric_stats(df)
        comp_df = pd.DataFrame(rows_m)

        _y_max    = comp_df["Media"].max()
        _y_min    = min(0, comp_df["Media"].min())
        _threshold = _y_max * 0.08
        comp_df["_label"] = comp_df["Media"].apply(
            lambda v: f"{v:,.3f}" if v >= _threshold else ""
        )

        fig_medias = px.bar(
            comp_df, x="Columna", y="Media",
            color="Distribución",
            color_discrete_map={
                "↑ Sesgada +": COLOR_SUCCESS,
                "↓ Sesgada −": COLOR_DANGER,
                "≈ Simétrica":  "#6B7280",
            },
            text="_label",
            title="Media por columna numérica",
        )
        fig_medias.update_traces(
            texttemplate="%{text}",
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(color="white", size=11),
        )
        fig_medias.update_layout(
            height=420,
            margin=dict(t=50, b=20, l=20, r=20),
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(tickfont=dict(color="#374151"), title=None, showgrid=False),
            yaxis=dict(tickfont=dict(color="#374151"), title="Media",
                       range=[_y_min, _y_max * 1.05],
                       showgrid=True, gridcolor="#E5E7EB"),
            legend=dict(title="Distribución", orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        st.plotly_chart(fig_medias, use_container_width=True)

        st.markdown("#### Detalle por columna")
        st.dataframe(
            comp_df.style.map(
                lambda v: "color: #10B981; font-weight:600" if v == "↑ Sesgada +"
                else ("color: #EF4444; font-weight:600" if v == "↓ Sesgada −" else "color: #6B7280"),
                subset=["Distribución"],
            ).format({"Media": "{:,.4f}", "Mediana": "{:,.4f}", "Desv. Est.": "{:,.4f}"}),
            use_container_width=True,
            hide_index=True,
        )

# ══ TAB 4: Correlaciones ══════════════════════════════════════════════════════

with tab_corr:
    numeric_cols_c = df.select_dtypes(include="number").columns.tolist()

    if len(numeric_cols_c) < 2:
        st.info("Necesitas al menos 2 columnas numéricas para calcular correlaciones.")
    else:
        selected_corr = st.multiselect(
            "Selecciona las columnas a analizar",
            options=numeric_cols_c,
            default=numeric_cols_c[:min(8, len(numeric_cols_c))],
            key="corr_cols",
            help="Selecciona 2 o más columnas numéricas",
        )

        if len(selected_corr) < 2:
            st.warning("Selecciona al menos 2 columnas para ver la matriz de correlación.")
        else:
            corr_matrix = _cached_correlation(df, tuple(selected_corr))

            _corr_vals  = corr_matrix.values
            _corr_labels = corr_matrix.columns.tolist()
            _annotations = []
            for _i, _row in enumerate(_corr_vals):
                for _j, _val in enumerate(_row):
                    _fc = "white" if abs(_val) > 0.45 else "#374151"
                    _annotations.append(dict(
                        x=_corr_labels[_j], y=_corr_labels[_i],
                        text=f"{_val:.3f}",
                        showarrow=False,
                        font=dict(color=_fc, size=12),
                        xref="x", yref="y",
                    ))

            fig_corr = go.Figure(data=go.Heatmap(
                z=_corr_vals,
                x=_corr_labels,
                y=_corr_labels,
                colorscale=[
                    [0.0,  "#B91C1C"],
                    [0.25, "#FCA5A5"],
                    [0.5,  "#F1F5F9"],
                    [0.75, "#93C5FD"],
                    [1.0,  "#1E40AF"],
                ],
                zmin=-1, zmax=1,
                xgap=3, ygap=3,
                colorbar=dict(
                    title=dict(text="r", side="right"),
                    tickvals=[-1, -0.7, -0.4, 0, 0.4, 0.7, 1],
                    ticktext=["-1", "-0.7", "-0.4", "0", "0.4", "0.7", "1"],
                    len=0.85,
                    thickness=14,
                    outlinewidth=0,
                ),
            ))
            fig_corr.update_layout(
                title=dict(text=f"Correlación de Pearson — {len(selected_corr)} columnas",
                           font=dict(size=15, color="#1F2937")),
                annotations=_annotations,
                height=max(380, len(selected_corr) * 60 + 80),
                margin=dict(t=55, b=20, l=20, r=100),
                paper_bgcolor="white",
                plot_bgcolor="white",
                xaxis=dict(tickfont=dict(color="#374151"), side="bottom"),
                yaxis=dict(tickfont=dict(color="#374151"), autorange="reversed"),
            )
            st.plotly_chart(fig_corr, use_container_width=True)

            st.markdown("#### Referencia de interpretación")
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.markdown("""
                **Correlación positiva** 🔵
                - `r ≥ 0.9` — Muy fuerte
                - `r ≥ 0.7` — Fuerte
                - `r ≥ 0.4` — Moderada
                """)
            with col_r2:
                st.markdown("""
                **Sin correlación** ⚪
                - `|r| < 0.4` — Débil / nula
                - `r = 0` — Sin relación lineal
                """)
            with col_r3:
                st.markdown("""
                **Correlación negativa** 🔴
                - `r ≤ -0.4` — Moderada
                - `r ≤ -0.7` — Fuerte
                - `r ≤ -0.9` — Muy fuerte
                """)

# ══ TAB 5: Historial ══════════════════════════════════════════════════════════

with tab_hist:
    change_log = st.session_state.model.change_log

    if change_log:
        st.markdown(f"#### {len(change_log)} operación(es) realizadas")
        st.caption("Las más recientes aparecen primero. Deshaz la última con **↩ Deshacer** en el panel izquierdo.")

        st.markdown('<ol role="list" style="list-style:none;padding:0;margin:0">', unsafe_allow_html=True)
        for idx, entry in enumerate(reversed(change_log)):
            num = len(change_log) - idx
            st.markdown(f"""
            <li role="listitem" class="log-entry">
                <span style="color:#6C63FF;font-weight:700">#{num}</span>
                &nbsp; {html.escape(entry)}
            </li>
            """, unsafe_allow_html=True)
        st.markdown('</ol>', unsafe_allow_html=True)

        st.markdown("")
        log_text = "\n".join(f"{i+1:02d}. {e}" for i, e in enumerate(change_log))
        st.download_button("📥 Descargar Log Completo (.txt)",
                           data=log_text.encode("utf-8"),
                           file_name="log_cambios.txt", mime="text/plain")
    else:
        st.markdown(_empty_state("📋",
            "Aún no se han realizado operaciones.",
            "Cada limpieza que apliques quedará registrada aquí."),
            unsafe_allow_html=True)
