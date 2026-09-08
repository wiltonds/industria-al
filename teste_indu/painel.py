import streamlit as st
from pathlib import Path
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Panorama Industrial AL",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "painel.html"

if not HTML_FILE.exists():
    st.error(f"Arquivo painel.html não encontrado em: {HTML_FILE}")
    st.stop()

html = HTML_FILE.read_text(encoding="utf-8")

components.html(
    html,
    height=1400,
    scrolling=True
)