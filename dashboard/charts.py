import streamlit as st
import pandas as pd
import plotly.colors as pc
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from core.data_loader import load_geojson

_MONTHS_RU_FULL = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)
_MONTHS_RU_SHORT = (
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
)


def _format_date_ru_full(value) -> str:
    d = pd.Timestamp(value).date()
    return f"{d.day} {_MONTHS_RU_FULL[d.month - 1]} {d.year}"


def _format_date_ru_short(value) -> str:
    d = pd.Timestamp(value).date()
    return f"{d.day} {_MONTHS_RU_SHORT[d.month - 1]}"


def _apply_ru_date_axis(fig, dates) -> None:
    unique = pd.to_datetime(pd.Series(dates)).drop_duplicates().sort_values()
    if len(unique) <= 20:
        fig.update_xaxes(
            tickmode="array",
            tickvals=unique,
            ticktext=[_format_date_ru_short(d) for d in unique],
            tickangle=-45,
        )
    else:
        fig.update_xaxes(tickformat="%d.%m.%Y", tickangle=-45)


CHART_HEIGHT = 420
MAP_ROW_HEIGHT = 580


def get_layout(title, height=None):
	layout = dict(
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
	if height is not None:
		layout["height"] = height
	return layout

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
    
    fig.update_layout(**get_layout(f"Распределение проблем по категориям{title_suffix}", CHART_HEIGHT))    
    
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
    fig.update_layout(**get_layout(f"Распределение проблем по муниципалитетам{title_suffix}", CHART_HEIGHT))    
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
    
    fig.update_layout(**get_layout(f"Классификация обращений{title_suffix}", CHART_HEIGHT), showlegend=True)    
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
    ts["Дата_рус"] = ts["Дата"].apply(_format_date_ru_full)
    
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
        **get_layout(f"Динамика обращений{title_suffix}", CHART_HEIGHT),
        xaxis_title="Дата",
        yaxis_title="Количество обращений",
        hovermode='x unified'
    )
    
    _apply_ru_date_axis(fig, ts["Дата"])

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
        **get_layout("Распределение обращений по муниципалитетам", CHART_HEIGHT),
        yaxis_title="",
        xaxis_title="Количество обращений"
    )
    
    return fig

# ТОП-10 диаграмма (универсальная)
def plot_top_10(
    df,
    title,
    category_col,
    color,
    highlight_municipality=None,
    highlight_match_col=None,
):
    def norm(x):
        return str(x).strip().lower() if pd.notnull(x) else ""

    match_col = highlight_match_col or category_col
    base_cols = [category_col, "количество_проблем"]
    if match_col in df.columns and match_col not in base_cols:
        top = (
            df[base_cols + [match_col]]
            .groupby(category_col, as_index=False)
            .agg({"количество_проблем": "sum", match_col: "first"})
        )
    else:
        top = (
            df[base_cols]
            .groupby(category_col, as_index=False)
            .sum()
        )
        match_col = category_col

    top = top.sort_values("количество_проблем", ascending=False).head(10)

    highlight_norm = norm(highlight_municipality)

    bar_colors = []
    for _, row in top.iloc[::-1].iterrows():
        if highlight_municipality and norm(row[match_col]) == highlight_norm:
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

    fig.update_layout(**get_layout(title, CHART_HEIGHT))

    return fig

def _severity_bar_color(value, vmin, vmax):
    if vmax <= vmin:
        return pc.sample_colorscale("Reds", [0.8])[0]
    t = (float(value) - vmin) / (vmax - vmin)
    return pc.sample_colorscale("Reds", [t])[0]


# Bar chart серьёзности
def create_bar_severity(df, highlight_municipality=None):
    agg = df.sort_values("сумма_тяжести", ascending=False).head(10).copy()
    severities = agg["средняя_тяжесть"].astype(float)
    vmin, vmax = severities.min(), severities.max()

    bar_colors = []
    line_colors = []
    line_widths = []
    custom_severity = []
    for _, row in agg.iterrows():
        is_highlight = highlight_municipality and row["муниципалитет"] == highlight_municipality
        if is_highlight:
            bar_colors.append("gold")
            line_colors.append("darkorange")
            line_widths.append(2)
        else:
            color = _severity_bar_color(row["средняя_тяжесть"], vmin, vmax)
            bar_colors.append(color)
            line_colors.append(color)
            line_widths.append(0)
        custom_severity.append(row["средняя_тяжесть"])

    fig = go.Figure(go.Bar(
        x=agg["муниципалитет"],
        y=agg["сумма_тяжести"],
        text=agg["количество_проблем"],
        textposition="outside",
        texttemplate="%{text} обращений",
        marker_color=bar_colors,
        marker_line_color=line_colors,
        marker_line_width=line_widths,
        customdata=custom_severity,
        hovertemplate="<b>%{x}</b><br>"
                      "Сумма тяжести: %{y}<br>"
                      "Количество проблем: %{text}<br>"
                      "Средняя тяжесть: %{customdata:.2f}<extra></extra>",
    ))
    
    fig.update_layout(**get_layout("ТОП-10 муниципалитетов: тяжесть", MAP_ROW_HEIGHT))
    fig.update_xaxes(title_text="Муниципалитет")
    fig.update_yaxes(title_text="Сумма тяжести")
    
    return fig