import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.express as px

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

def create_problem_pie(df):
	themes = (
		df["Группа тем"]
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

	fig.update_layout(**get_layout("Распределение проблем по категориям"))	

	return fig

def create_municipality_sunburst(df):
	"""
	Sunburst:
	Населенный пункт -> Муниципалитет
	Размер сектора = количество обращений
	"""

	sunburst_data = (
		df.groupby(
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
	fig.update_layout(**get_layout("Распределение проблем по муниципалитетам"))	
	return fig

def get_top3_districts(df):
	top3 = (
		df["Населенный пункт"]
		.value_counts()
		.head(3)
		.index
	)

	result = []

	for district in top3:

		district_df = df[
			df["Населенный пункт"] == district
		]

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


def plot_classification(df):
	counts = df["Проблема"].value_counts()

	fig = go.Figure(data=[
		go.Pie(
			labels=["Проблемные", "Не проблемные"],
			values=[counts.get(True, 0), counts.get(False, 0)],
			hole=0.6,
			marker_colors=["#EF4444", "#22C55E"]
		)
	])

	fig.update_layout(**get_layout("Классификация обращений"), showlegend=True)	

	st.plotly_chart(fig, use_container_width=True)

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def plot_dynamics(df):
	df["Дата создания"] = pd.to_datetime(df["Дата создания"])
	ts = df.groupby(df["Дата создания"].dt.date).size().reset_index()
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
	
	# Настройка осей с русскими названиями
	fig.update_layout(
		**get_layout("Динамика обращений"),
		xaxis_title="Дата",
		yaxis_title="Количество обращений",
		hovermode='x unified'
	)
	
	fig.update_xaxes(
		tickformat="%d %b",
		tickangle=-45
	)
	
	st.plotly_chart(fig, use_container_width=True)

def create_municipality_chart(df):
	data = (
		df.groupby("Муниципалитет")
		.size()
		.reset_index(name="Количество")
		.sort_values("Количество", ascending=True)
		.tail(15)
	)

	fig = px.bar(
		data,
		x="Количество",
		y="Муниципалитет",
		orientation="h",
		text="Количество",
		title="ТОП муниципалитетов по числу обращений"
	)

	fig.update_traces(textposition="outside")
	fig.update_layout(
		**get_layout("Распределение обращений по муниципалитетам"),
		yaxis_title="",
		xaxis_title="Количество обращений"
	)

	return fig

def plot_top_10(df, title, category_col, color):
	top = (
		df[[category_col, "количество_проблем",]]
		.sort_values("количество_проблем", ascending=False)
		.head(10)
	)

	fig = go.Figure(go.Bar(
		x=top["количество_проблем"].values[::-1],
		y=top[category_col].values[::-1],
		orientation="h",
		marker_color=color
	))

	fig.update_layout(**get_layout(title))

	return fig

def create_bar_severity(df):

	agg = df.sort_values("сумма_тяжести", ascending=False).head(10)

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

	return fig