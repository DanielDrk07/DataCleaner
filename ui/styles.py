import streamlit as st

_CSS = """
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
"""


def inject_styles() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
