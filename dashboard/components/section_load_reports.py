import streamlit as st

from components.downloads import columns_dowload_buttons
from core.report_context import get_active_report_dir

def load_reports():
  st.subheader("Скачать отчёты")
  active_dir = get_active_report_dir()
  if active_dir:
    st.caption(f"Папка: **{active_dir.name}**")
  columns_dowload_buttons();