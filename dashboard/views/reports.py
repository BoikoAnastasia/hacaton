import streamlit as st

from core.config import DATA_FILE_SUMMARY
from core.data_loader import load_main_df
from utils.cleaning_stats import load_cleaning_stats
from components.cleaning_info import render_cleaning_info
from components.downloads import columns_dowload_buttons
from analytics import get_kpi_metrics
from components.kpi import render_kpi_cards
from components.table import create_table

def render_reports():
  df = load_main_df()

  kpi = None

  if df is not None:
    kpi = get_kpi_metrics(df, load_cleaning_stats())

  st.subheader("Результат анализа")

  if kpi is not None:
    render_kpi_cards(kpi)
    render_cleaning_info(kpi.get("cleaning_stats"))
  else:
    st.warning("KPI не рассчитан")

  st.subheader("Скачать отчёты")
  columns_dowload_buttons();

  st.subheader("Справка для руководства")

  if DATA_FILE_SUMMARY.exists():
    with open(DATA_FILE_SUMMARY, "rb") as f:
      st.pdf(f.read(), height=720)
  else:
    st.info("PDF-справка появится после завершения анализа.")

  create_table(df)


