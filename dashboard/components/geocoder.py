import pandas as pd
import plotly.express as px
from pathlib import Path

from core.data_loader import load_geojson
from utils.problem import is_problem

MAP_BG = "#111827"
MAP_BORDER = "#1f2937"
NO_DATA_COLOR = "#1f2937"

COUNT_SCALE = [
  [0.0, NO_DATA_COLOR],
  [0.05, "#fee5d9"],
  [0.35, "#fc9272"],
  [0.65, "#de2d26"],
  [1.0, "#99000d"],
]


# Подготовка данных Excel
def prepare_data(df):
  df = df.copy()

  df["Серьёзность"] = pd.to_numeric(df["Серьёзность"], errors="coerce")
  df["Муниципалитет"] = df["Муниципалитет"].astype(str).str.strip()

  if "Проблема" in df.columns:
    work = df[df["Проблема"].apply(is_problem)]
  else:
    work = df

  agg = (
    work.groupby("Муниципалитет", dropna=False)
    .agg(
      count=("Серьёзность", "size"),
      severity=("Серьёзность", "mean"),
    )
    .reset_index()
  )

  total = int(agg["count"].sum())
  agg["percent"] = (agg["count"] / total * 100).round(1) if total else 0.0
  agg["severity"] = agg["severity"].round(2)

  return agg


def _merge_all_municipalities(agg: pd.DataFrame, geojson: dict) -> pd.DataFrame:
  """Все районы области на карте, даже без обращений в выборке."""
  municipalities = sorted(
    feature["properties"]["mun_name"]
    for feature in geojson["features"]
    if feature["properties"].get("mun_name")
  )
  base = pd.DataFrame({"Муниципалитет": municipalities})
  merged = base.merge(agg, on="Муниципалитет", how="left")
  merged["count"] = merged["count"].fillna(0).astype(int)
  merged["percent"] = merged["percent"].fillna(0.0)
  merged["severity"] = merged["severity"].fillna(0.0)
  return merged


# Построение карты
def plot_omsk_choropleth(df):
  geojson_path = Path(__file__).resolve().parent.parent / "data" / "omsk.json"
  geojson = load_geojson(geojson_path)
  data = _merge_all_municipalities(prepare_data(df), geojson)

  max_count = int(data["count"].max() or 1)

  fig = px.choropleth(
    data,
    geojson=geojson,
    locations="Муниципалитет",
    featureidkey="properties.mun_name",
    color="count",
    color_continuous_scale=COUNT_SCALE,
    range_color=[0, max_count],
    hover_data={
      "percent": True,
      "severity": True,
    },
    labels={
      "count": "Проблемных обращений",
      "percent": "Доля от всех проблем (%)",
      "severity": "Средняя тяжесть",
      "Муниципалитет": "Район",
    },
  )

  fig.update_layout(
    height=580,
    margin=dict(l=4, r=48, t=4, b=4),
    dragmode="zoom",
    paper_bgcolor=MAP_BG,
    plot_bgcolor=MAP_BG,
    font=dict(color="#e5e7eb"),
    coloraxis_colorbar=dict(
      title=dict(text="Проблем", font=dict(color="#e5e7eb")),
      bgcolor=MAP_BG,
      bordercolor=MAP_BORDER,
      tickfont=dict(color="#9ca3af"),
    ),
  )

  fig.update_geos(
    fitbounds="locations",
    domain=dict(x=[0.0, 0.88], y=[0.0, 1.0]),
    visible=False,
    bgcolor=MAP_BG,
    landcolor=MAP_BG,
    lakecolor=MAP_BG,
    subunitcolor=MAP_BG,
    countrycolor=MAP_BG,
    coastlinecolor=MAP_BG,
    projection_type="mercator",
  )

  fig.update_traces(
    marker_line_color="#6b7280",
    marker_line_width=0.5,
    showlegend=False,
  )

  return fig
