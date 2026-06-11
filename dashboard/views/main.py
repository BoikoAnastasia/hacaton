import streamlit as st

from charts import (get_top3_districts)
from analytics import (get_kpi_metrics, get_severity_stats)

from components.downloads import columns_dowload_buttons
from components.top3_districts import get_top3_districts
from components.district_card import render_top_district_card
from components.table import create_table
from components.kpi import render_kpi_cards

from core.data_loader import load_main_df
from utils.cleaning_stats import load_cleaning_stats
from components.cleaning_info import render_cleaning_info

def render_main():
    df = load_main_df()

    empty = {"count": 0, "percent": 0}
    kpi = None
    high = empty.copy()
    medium = empty.copy()
    low = empty.copy()

    if df is not None:
        kpi = get_kpi_metrics(df, load_cleaning_stats())
        severity = get_severity_stats(df)
        high = severity["high"]
        medium = severity["medium"]
        low = severity["low"]

    st.subheader("Скачать отчёты")
    columns_dowload_buttons();

    st.subheader("Ключевые показатели")

    if kpi is not None:
        render_kpi_cards(kpi)
        render_cleaning_info(kpi.get("cleaning_stats"))
    else:
        st.warning("Загрузите файл в боковой панели и нажмите «Запустить анализ».")
        return

    st.subheader("Распределение по степени тяжести")

    left, center, right = st.columns([1, 1, 1])

    with left:
        st.markdown(f"""
        <div class="severity-card severity-high">
            <div style="font-size: 20px; color: #EF4444;">
                Высокая (4-5)
            </div>
            <div style="font-size: 34px;">
                <span>{high["count"]}</span>
                <span style="font-size: 20px;">
                    проблем
                </span>
                <div>
                    {high["percent"]}% всех проблем
                </div>
            </div>
            <div style="font-size: 18px; color: var(--grey);">
                Требуют немедленного решения
            </div> 
            <div class="severity-bar">
                <div class="severity-fill high"
                    style="width:{high["percent"]}%">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with center:
        st.markdown(f"""
        <div class="severity-card severity-medium">
            <div style="font-size: 20px; color: #F59E0B;">
                Средняя (2-3)
            </div>
            <div style="font-size: 34px;">
                <span>{medium["count"]}</span>
                <span style="font-size: 20px;">
                    проблем
                </span>
                <div>
                    {medium["percent"]}% всех проблем
                </div>
            </div>
            <div style="font-size: 18px; color: var(--grey);">
                Требуют внимания    
            </div>
            <div class="severity-bar">
                <div class="severity-fill medium"
                    style="width:{medium["percent"]}%">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown(f"""
        <div class="severity-card severity-low">
            <div style="font-size: 20px; color: #22C55E;">
                Низкая (0-1)
            </div>
            <div style="font-size: 34px;">
                <span>{low["count"]}</span>
                <span style="font-size: 20px;">
                    проблем
                </span>
                <div>
                    {low["percent"]}% всех проблем
                </div>
            </div>
            <div style="font-size: 18px; color: var(--grey);">
                Плавые задачи
            </div>
            <div class="severity-bar">
                <div class="severity-fill low"
                    style="width:{low["percent"]}%">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


    st.subheader("ТОП-3 проблемных района")

    cols = st.columns(3)
    top3 = get_top3_districts(df)
    for col, item in zip(cols, top3):
        with col:
            st.markdown(
                render_top_district_card(
                    rank=item["rank"],
                    district=item["district"],
                    count=item["count"],
                    severity=item["severity"],
                    problems=item["problems"]
                ),
                unsafe_allow_html=True
            )

    create_table(df, 10, show_full_table_button=True)