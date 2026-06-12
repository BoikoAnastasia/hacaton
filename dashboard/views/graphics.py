import streamlit as st
from charts import (
    create_problem_pie,
    plot_top_10,
    create_municipality_chart,
    create_bar_severity,
    plot_classification,
    plot_dynamics,
)

from components.geocoder import plot_omsk_choropleth
from analytics import get_kpi_metrics
from components.kpi import render_kpi_cards
from core.data_loader import load_main_df, load_top10_df
from utils.cleaning_stats import load_cleaning_stats

_MAP_CONFIG = {
    "scrollZoom": True,
    "displayModeBar": False,
    "doubleClick": "reset",
}


def render_graphics():
    df = load_main_df()
    df10 = load_top10_df()

    st.subheader("Визуальное представление анализа")

    selected_area = st.selectbox(
        "Выберите муниципалитет для фильтрации",
        ["Все"] + sorted(df["Муниципалитет"].dropna().unique()),
        key="municipality_filter",
    )

    highlight_municipality = None if selected_area == "Все" else selected_area
    kpi = None
    if df is not None:
        kpi = get_kpi_metrics(df, load_cleaning_stats())
    if kpi is not None:
        render_kpi_cards(kpi)
    else:
        st.warning("KPI не рассчитан")

    if df is None:
        st.info("Графики появятся после завершения анализа.")
        return


    row1_l, row1_r = st.columns(2)
    with row1_l:
        st.plotly_chart(
            plot_omsk_choropleth(df, highlight_municipality=highlight_municipality),
            use_container_width=True,
            key="omsk_choropleth_map",
            config=_MAP_CONFIG,
        )

    with row1_r:
        st.plotly_chart(
            create_bar_severity(df10, highlight_municipality=highlight_municipality),
            use_container_width=True,
            key="graphics_bar_severity",
        )


    row2_l, row2_r = st.columns(2)
    with row2_l:
        st.plotly_chart(
            plot_top_10(
                df10,
                "ТОП-10 проблемных муниципалитетов",
                "муниципалитет",
                "#EF4444",
                highlight_municipality=highlight_municipality,
            ),
            use_container_width=True,
            key="graphics_top10_municipalities",
        )

    with row2_r:
        st.plotly_chart(
            plot_top_10(
                df10,
                "ТОП-10 проблемных районов",
                "район",
                "#8B5CF6",
                highlight_municipality=highlight_municipality,
                highlight_match_col="муниципалитет",
            ),
            use_container_width=True,
            key="graphics_top10_districts",
        )



    row3_l, row3_r = st.columns(2)
    with row3_l:
        st.plotly_chart(
            create_municipality_chart(df, highlight_municipality=highlight_municipality),
            use_container_width=True,
            key="graphics_municipality_chart",
        )

    with row3_r:
        st.plotly_chart(
            create_problem_pie(df, highlight_municipality=highlight_municipality),
            use_container_width=True,
            key="graphics_problem_pie",
        )


    row4_l, row4_r = st.columns(2)
    with row4_l:
        st.plotly_chart(
            plot_classification(df, highlight_municipality=highlight_municipality),
            use_container_width=True,
            key="graphics_classification",
        )

    with row4_r:
        st.plotly_chart(
            plot_dynamics(df, highlight_municipality=highlight_municipality),
            use_container_width=True,
            key="graphics_dynamics",
        )


