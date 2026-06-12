import streamlit as st

from components.sidebar import sidebar
from views.main import render_main
from views.graphics import render_graphics
from views.reports import render_reports
from views.compare import render_compare

if "page" not in st.session_state:
    st.session_state.page = "main"

st.set_page_config(
    page_title="Аналитика обращений граждан",
    page_icon="./assets/icons/chart-bar-big-columns.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

with open("./assets/style/style.css") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )

sidebar()

page = st.session_state.page

if page == "main":
    render_main()

elif page == "graphics":
    render_graphics()

elif page == "reports":
    render_reports()

elif page == "compare":
    render_compare()