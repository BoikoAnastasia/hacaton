import streamlit as st

from utils.load_llm_summary import load_llm_summary
from core.data_loader import load_main_df, load_top10_df
from components.downloads import columns_dowload_buttons
from analytics import get_kpi_metrics
from components.kpi import render_kpi_cards
from components.table import create_table

def render_reports():
  df = load_main_df()

  kpi = None

  if df is not None:
    kpi = get_kpi_metrics(df)

  st.subheader("Результат анализа")

  if kpi is not None:
    render_kpi_cards(kpi)
  else:
    st.warning("KPI не рассчитан")

  st.subheader("Скачать отчёты")
  columns_dowload_buttons();

  st.subheader("Общие выводы по загруженному файлу")

  summary = load_llm_summary()

  st.markdown(summary)

  create_table(df)


