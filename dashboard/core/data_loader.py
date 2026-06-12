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

def geojson_bounds(geojson: dict, padding: float = 0.06) -> dict[str, float]:
  """Границы полигонов для fit-to-view (вся область в кадре)."""
  lons: list[float] = []
  lats: list[float] = []

  def walk(coords):
    if isinstance(coords[0], (int, float)):
      lons.append(float(coords[0]))
      lats.append(float(coords[1]))
    else:
      for part in coords:
        walk(part)

  for feature in geojson.get("features", []):
    geometry = feature.get("geometry")
    if geometry:
      walk(geometry["coordinates"])

  if not lons:
    return {"west": 70.4, "east": 76.3, "south": 53.4, "north": 58.6}

  west, east = min(lons), max(lons)
  south, north = min(lats), max(lats)
  pad_lon = (east - west) * padding
  pad_lat = (north - south) * padding
  return {
    "west": west - pad_lon,
    "east": east + pad_lon,
    "south": south - pad_lat,
    "north": north + pad_lat,
  }


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
