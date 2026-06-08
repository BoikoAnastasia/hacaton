import streamlit as st
import pandas as pd
import base64

from components.nav_button import nav_button

def sidebar():
  with st.sidebar:
    with open("./assets/icons/file-report.png", "rb") as f:
      img_base64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
      <div style="
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
      ">
        <img
          src="data:image/png;base64, {img_base64}"
          width="45"
          height="45"
          >          
          <div style="
            font-size: 20px;
            font-weight: 700;
            color: white;
            text-align: center;
          ">
            Аналитика обращений граждан
          </div>
      </div>  
    """, unsafe_allow_html=True)
    nav_button("Главная", "main")
    nav_button("Анализ", "graphics")
    nav_button("Отчёты", "reports")

    st.divider()

    with st.container():
      uploaded_file = st.file_uploader(
        "Загрузить Excel файл для анализа",
        type=["xlsx"]
      )

      if st.button(
        "Запустить анализ",
        key="run_analysis",
        use_container_width=True
      ):
        if uploaded_file is not None:
          st.session_state.df = pd.read_excel(
            uploaded_file
          )
