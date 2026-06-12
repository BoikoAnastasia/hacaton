import streamlit as st

from charts import (
    create_problem_pie, 
    plot_top_10, 
    create_municipality_chart, 
    create_bar_severity, 
    plot_classification, 
    plot_dynamics,
    create_municipality_sunburst
)
from components.geocoder import plot_omsk_choropleth
from analytics import get_kpi_metrics
from components.kpi import render_kpi_cards
from core.data_loader import load_main_df, load_top10_df
from utils.cleaning_stats import load_cleaning_stats

def render_graphics():
    df = load_main_df()
    df10 = load_top10_df()
    
    # Селектор для выбора муниципалитета (без фильтрации данных)
    selected_area = st.selectbox(
        "Выберите муниципалитет для подсветки",
        ["Все"] + sorted(df["Муниципалитет"].dropna().unique()),
        key="municipality_filter"
    )
    
    # Определяем, какой муниципалитет подсвечивать
    highlight_municipality = None if selected_area == "Все" else selected_area
    
    # KPI считаем на всех данных
    kpi = None
    if df is not None:
        kpi = get_kpi_metrics(df, load_cleaning_stats())
    
    st.subheader("Результат анализа")
    
    if kpi is not None:
        render_kpi_cards(kpi)
    else:
        st.warning("KPI не рассчитан")
    
    col1, col2 = st.columns(2)
    
    with col1:
      if df is not None:
        st.plotly_chart(
          plot_omsk_choropleth(df, highlight_municipality=highlight_municipality),  # ← Добавить параметр
          use_container_width=True,
          key="omsk_choropleth_map",
          config={
            "scrollZoom": True,
            "displayModeBar": False,
            "doubleClick": "reset",
          },
        )
        st.plotly_chart(
          plot_top_10(df10, "ТОП-10 проблемных муниципалитетов", "муниципалитет", "#EF4444", highlight_municipality=highlight_municipality),
          use_container_width=True
        )
        st.plotly_chart(
          create_municipality_chart(df, highlight_municipality=highlight_municipality),
          use_container_width=True
        )
        st.plotly_chart(
          plot_classification(df, highlight_municipality=highlight_municipality),
          use_container_width=True
        )
    
      else:
        st.info("Карта появится после завершения анализа.")
        
    with col2:
        st.plotly_chart(
            create_bar_severity(df10, highlight_municipality=highlight_municipality), 
            use_container_width=True
        )
        st.plotly_chart(
            plot_top_10(df10, "ТОП-10 проблемных районов", "район", "#8B5CF6", highlight_municipality=highlight_municipality),
            use_container_width=True
        )
        st.plotly_chart(
            create_problem_pie(df, highlight_municipality=highlight_municipality),
            use_container_width=True
        )
        st.plotly_chart(
            plot_dynamics(df, highlight_municipality=highlight_municipality),
            use_container_width=True
        )