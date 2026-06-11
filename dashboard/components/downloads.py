import streamlit as st

from core.config import DATA_FILE_SUMMARY, DATA_FILE_TOP_10, DATA_FILE_RESULT
from utils.make_zip import make_zip

def columns_dowload_buttons():
  col1, col2, col3, col4 = st.columns(4)
  # 1 — Excel result
  with col1:
    if DATA_FILE_RESULT.exists():
      with open(DATA_FILE_RESULT, "rb") as f:
        st.download_button(
          "Полный Excel",
          data=f,
          file_name="result.xlsx"
        )

  # 2 — Top10 Excel
  with col2:
    if DATA_FILE_TOP_10.exists():
      with open(DATA_FILE_TOP_10, "rb") as f:
        st.download_button(
          "Топ 10 Excel",
          data=f,
          file_name="report.xlsx"
        )

  # 3 — PDF-справка
  with col3:
    if DATA_FILE_SUMMARY.exists():
      with open(DATA_FILE_SUMMARY, "rb") as f:
        st.download_button(
          "Справка PDF",
          data=f,
          file_name="report.pdf",
          mime="application/pdf",
        )

  # 4 — ZIP (всё вместе)
  with col4:
    files = []

    if DATA_FILE_RESULT.exists():
      files.append(DATA_FILE_RESULT)

    if DATA_FILE_TOP_10.exists():
      files.append(DATA_FILE_TOP_10)

    if DATA_FILE_SUMMARY.exists():
      files.append(DATA_FILE_SUMMARY)

    if files:
      zip_buffer = make_zip(files)

      st.download_button(
        "Скачать всё",
        data=zip_buffer,
        file_name="reports.zip",
        mime="application/zip",
        key="dl_all"
      )
