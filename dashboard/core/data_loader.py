import pandas as pd
import json
from core.report_files import KIND_REPORT, KIND_RESULT, find_report_file

def load_main_df():
  path = find_report_file(KIND_RESULT)
  if path:
    return pd.read_excel(path)
  return None

def load_top10_df():
  path = find_report_file(KIND_REPORT)
  if path:
    return pd.read_excel(path)
  return None

# Загрузка GeoJSON (Омская область + районы)
def load_geojson(path):
  with open(path, "r", encoding="utf-8") as f:
    geojson = json.load(f)

  features = [
    f for f in geojson["features"]
    if f["properties"]["NAME_1"] == "Omsk"
  ]

  for f in features:
    name = f["properties"].get("NL_NAME_2", "").strip()
    name = name.replace("район", " район").strip()
    f["properties"]["mun_name"] = name

  return {
    "type": "FeatureCollection",
    "features": features
  }
