import pandas as pd
import plotly.express as px
from pathlib import Path

from core.data_loader import load_geojson

# Подготовка данных Excel
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

# Построение карты
def plot_omsk_choropleth(df):
  geojson_path = Path(__file__).resolve().parent.parent / "data" / "omsk.json"
  data = prepare_data(df)
  geojson = load_geojson(geojson_path)
  
  # Фильтруем данные по муниципалитетам из GeoJSON
  valid_municipalities = set()
  for feature in geojson["features"]:
    mun_name = feature["properties"].get("mun_name")
    if mun_name:
      valid_municipalities.add(mun_name)
  data = data[data["Муниципалитет"].isin(valid_municipalities)]
  
  fig = px.choropleth_mapbox(
    data,
    geojson=geojson,
    locations="Муниципалитет",
    featureidkey="properties.mun_name",
    
    color="severity",
    color_continuous_scale="Reds",
    
    hover_data={
      "count": True,
      "percent": True,
      "severity": True
    },
    
    labels={
      "count": "Количество обращений",
      "percent": "Доля (%)",
      "severity": "Средняя серьёзность"
    },
    
    mapbox_style="white-bg",
    zoom=5.5,
    center={"lat": 56.5, "lon": 73.0},
    opacity=0.75
  )
  
  fig.update_layout(
    margin=dict(r=0, t=0, l=0, b=0),
    dragmode="zoom",
    uirevision="constant",
    paper_bgcolor="#111827", 
    plot_bgcolor="#111827 " 
  )
  
  fig.update_traces(
    marker_line_color="black",
    marker_line_width=0.5,
    showlegend=False
  )
  
  return fig
