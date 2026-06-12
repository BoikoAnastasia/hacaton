import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from core.data_loader import load_geojson

def get_layout(title):
	return dict(
		title=dict(
			text=title,
			x=0.5,
			xanchor="center",
			font=dict(size=24, color="white")
		),
		paper_bgcolor="#111827",
		plot_bgcolor="#111827",
		font_color="white",
		margin=dict(t=80, l=20, r=20, b=20),
	)

# Подготовка данных для карты
def prepare_data(df):
    df = df.copy()
    df["Серьёзность"] = pd.to_numeric(df["Серьёзность"], errors="coerce")
    
    agg = (
        df.groupby("Муниципалитет")
        .agg(
            count=("Серьёзность", "size"),
            severity=("Серьёзность", "mean")
        )
        .reset_index()
    )
    
    agg["Муниципалитет"] = agg["Муниципалитет"].str.strip()
    total = agg["count"].sum()
    agg["percent"] = (agg["count"] / total * 100).round(1)
    
    return agg

# Круговая диаграмма проблем
def create_problem_pie(df, highlight_municipality=None):
    if highlight_municipality:
        df_filtered = df[df["Муниципалитет"] == highlight_municipality]
        title_suffix = f" (выделен: {highlight_municipality})"
    else:
        df_filtered = df
        title_suffix = ""
    
    themes = (
        df_filtered["Группа тем"]
        .value_counts()
        .reset_index()
    )
    
    themes.columns = ["Категория", "Количество"]
    
    fig = px.pie(
        themes,
        names="Категория",
        values="Количество",
        hole=0.55
    )
    
    fig.update_traces(
        textinfo="label+percent",
        textposition="inside"
    )
    
    fig.update_layout(**get_layout(f"Распределение проблем по категориям{title_suffix}"))    
    
    return fig

# Sunburst диаграмма
def create_municipality_sunburst(df, highlight_municipality=None):
    if highlight_municipality:
        df_filtered = df[df["Муниципалитет"] == highlight_municipality]
        title_suffix = f" (выделен: {highlight_municipality})"
    else:
        df_filtered = df
        title_suffix = ""
    
    sunburst_data = (
        df_filtered.groupby(
            ["Населенный пункт", "Муниципалитет"]
        )
        .size()
        .reset_index(name="Количество")
    )
    
    fig = px.sunburst(
        sunburst_data,
        path=["Населенный пункт", "Муниципалитет"],
        values="Количество",
        title="Распределение проблем по муниципалитетам"
    )
    fig.update_layout(**get_layout(f"Распределение проблем по муниципалитетам{title_suffix}"))    
    return fig

# ТОП-3 районов
def get_top3_districts(df, highlight_municipality=None):
    if highlight_municipality:
        df_filtered = df[df["Муниципалитет"] == highlight_municipality]
    else:
        df_filtered = df
    
    top3 = (
        df_filtered["Населенный пункт"]
        .value_counts()
        .head(3)
        .index
    )
    
    result = []
    for district in top3:
        district_df = df_filtered[df_filtered["Населенный пункт"] == district]
        top_problems = (
            district_df["Группа тем"]
            .value_counts()
            .head(3)
            .index
            .tolist()
        )
        
        result.append({
            "district": district,
            "count": len(district_df),
            "problems": top_problems
        })
    
    return result

# Классификация обращений
def plot_classification(df, highlight_municipality=None):
    if highlight_municipality:
        df_filtered = df[df["Муниципалитет"] == highlight_municipality]
        title_suffix = f" (выделен: {highlight_municipality})"
    else:
        df_filtered = df
        title_suffix = ""
    
    counts = df_filtered["Проблема"].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=["Проблемные", "Не проблемные"],
            values=[counts.get(True, 0), counts.get(False, 0)],
            hole=0.6,
            marker_colors=["#EF4444", "#22C55E"]
        )
    ])
    
    fig.update_layout(**get_layout(f"Классификация обращений{title_suffix}"), showlegend=True)    
    return fig

# Динамика обращений
def plot_dynamics(df, highlight_municipality=None):
    if highlight_municipality:
        df_filtered = df[df["Муниципалитет"] == highlight_municipality]
        title_suffix = f" (выделен: {highlight_municipality})"
    else:
        df_filtered = df
        title_suffix = ""
    
    df_filtered = df_filtered.copy()
    df_filtered["Дата создания"] = pd.to_datetime(df_filtered["Дата создания"])
    ts = df_filtered.groupby(df_filtered["Дата создания"].dt.date).size().reset_index()
    ts.columns = ["Дата", "Количество"]
    
    # Создаём словарь для перевода месяцев на русский
    months_ru = {
        'January': 'января', 'February': 'февраля', 'March': 'марта',
        'April': 'апреля', 'May': 'мая', 'June': 'июня',
        'July': 'июля', 'August': 'августа', 'September': 'сентября',
        'October': 'октября', 'November': 'ноября', 'December': 'декабря'
    }
    
    # Форматируем даты для отображения на русском
    ts["Дата_рус"] = ts["Дата"].apply(
        lambda x: f"{x.day} {months_ru[x.strftime('%B')]} {x.year}"
    )
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=ts["Дата"],
        y=ts["Количество"],
        mode="lines+markers",
        line=dict(color="#8B5CF6", width=3),
        marker=dict(size=8, color="#8B5CF6"),
        text=ts["Дата_рус"],
        hovertemplate='<b>%{text}</b><br>Обращений: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        **get_layout(f"Динамика обращений{title_suffix}"),
        xaxis_title="Дата",
        yaxis_title="Количество обращений",
        hovermode='x unified'
    )
    
    fig.update_xaxes(
        tickformat="%d %b",
        tickangle=-45
    )
    
    return fig

# Горизонтальная бар-диаграмма муниципалитетов
def create_municipality_chart(df, highlight_municipality=None):
    data = (
        df.groupby("Муниципалитет")
        .size()
        .reset_index(name="Количество")
        .sort_values("Количество", ascending=True)
        .tail(15)
    )
    
    # Создаём цвета для баров
    if highlight_municipality:
        colors = ["#EF4444" if x == highlight_municipality else "#6B7280" for x in data["Муниципалитет"]]
    else:
        colors = "#EF4444"
    
    fig = px.bar(
        data,
        x="Количество",
        y="Муниципалитет",
        orientation="h",
        text="Количество",
        title="ТОП муниципалитетов по числу обращений",
        color_discrete_sequence=[colors] if isinstance(colors, str) else colors
    )
    
    fig.update_traces(
        textposition="outside",
        marker_color=colors
    )
    
    fig.update_layout(
        **get_layout("Распределение обращений по муниципалитетам"),
        yaxis_title="",
        xaxis_title="Количество обращений"
    )
    
    return fig

# ТОП-10 диаграмма (универсальная)
def plot_top_10(df, title, category_col, color, highlight_municipality=None):

    def norm(x):
        return str(x).strip().lower() if pd.notnull(x) else ""

    top = (
        df[[category_col, "количество_проблем"]]
        .groupby(category_col, as_index=False)
        .sum()
        .sort_values("количество_проблем", ascending=False)
        .head(10)
    )

    highlight_norm = norm(highlight_municipality)

    bar_colors = []
    for val in top[category_col].values[::-1]:
        if highlight_municipality and norm(val) == highlight_norm:
            bar_colors.append("gold")
        else:
            bar_colors.append(color)

    fig = go.Figure(go.Bar(
        x=top["количество_проблем"].values[::-1],
        y=top[category_col].values[::-1],
        orientation="h",
        marker_color=bar_colors,
        text=top["количество_проблем"].values[::-1],
        textposition="outside"
    ))

    fig.update_layout(**get_layout(title))

    return fig

# Bar chart серьёзности
def create_bar_severity(df, highlight_municipality=None):
    agg = df.sort_values("сумма_тяжести", ascending=False).head(10)
    
    if highlight_municipality:
        # Создаём колонку с цветами для каждого бара
        agg["bar_color"] = agg.apply(
            lambda x: "gold" if x["муниципалитет"] == highlight_municipality else x["средняя_тяжесть"],
            axis=1
        )
        
        # Создаём два отдельных графика: один для обычных, один для выделенного
        fig = go.Figure()
        
        # Добавляем все бары, кроме выделенного
        mask_not_highlight = agg["муниципалитет"] != highlight_municipality
        if mask_not_highlight.any():
            fig.add_trace(go.Bar(
                x=agg[mask_not_highlight]["муниципалитет"],
                y=agg[mask_not_highlight]["сумма_тяжести"],
                text=agg[mask_not_highlight]["количество_проблем"],
                textposition="outside",
                marker_color=agg[mask_not_highlight]["средняя_тяжесть"],
                marker_colorscale="Reds",
                name="Другие муниципалитеты",
                hovertemplate='<b>%{x}</b><br>'
                              'Сумма тяжести: %{y}<br>'
                              'Количество проблем: %{text}<br>'
                              'Средняя тяжесть: %{marker.color:.2f}<extra></extra>'
            ))
        
        # Добавляем выделенный бар отдельно (золотой)
        mask_highlight = agg["муниципалитет"] == highlight_municipality
        if mask_highlight.any():
            highlight_data = agg[mask_highlight]
            fig.add_trace(go.Bar(
                x=highlight_data["муниципалитет"],
                y=highlight_data["сумма_тяжести"],
                text=highlight_data["количество_проблем"],
                textposition="outside",
                marker_color="gold",
                name=f"{highlight_municipality} (выделен)",
                marker_line_color="darkorange",
                marker_line_width=2,
                hovertemplate='<b>%{x}</b><br>'
                              'Сумма тяжести: %{y}<br>'
                              'Количество проблем: %{text}<br>'
            ))
        
        fig.update_layout(barmode='group')
        
    else:
        # Обычный px.bar
        fig = px.bar(
            agg,
            x="муниципалитет",
            y="сумма_тяжести",
            color="средняя_тяжесть",
            color_continuous_scale="Reds",
            text="количество_проблем"
        )
        fig.update_traces(texttemplate="%{text} обращений", textposition="outside")
    
    fig.update_layout(**get_layout("ТОП-10 муниципалитетов: тяжесть"))
    fig.update_xaxes(title_text="Муниципалитет")
    fig.update_yaxes(title_text="Сумма тяжести")
    
    return fig