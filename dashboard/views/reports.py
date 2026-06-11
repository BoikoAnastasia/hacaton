import streamlit as st

from core.report_context import get_active_report_dir
from core.data_loader import load_main_df
from utils.cleaning_stats import load_cleaning_stats
from components.cleaning_info import render_cleaning_info
from analytics import get_kpi_metrics
from components.kpi import render_kpi_cards
from components.table import create_table
from utils.summary_text import load_leadership_summary_text

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

  active_dir = get_active_report_dir()
  if active_dir:
    st.caption(
      f"Папка отчёта: **{active_dir.name}** · "
      "PDF-справка и остальные файлы — на главной"
    )

  st.subheader("Краткая сводка")

  summary_text = load_leadership_summary_text()
  if summary_text:
    st.text(summary_text)
  else:
    st.info("Краткая сводка появится после завершения анализа.")

  create_table(df)


