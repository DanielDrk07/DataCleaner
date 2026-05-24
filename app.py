"""
DataCleaner — entry point
Ejecutar con: streamlit run app.py
"""
import sys
import os

# Permite importar model/ y ui/ desde cualquier directorio de trabajo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st

from ui.styles import inject_styles
from ui.utils import _init_state
from ui.sidebar import render_sidebar
from ui.tabs import render_tabs

st.set_page_config(
    page_title="DataCleaner",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()
_init_state()
render_sidebar()
render_tabs()
