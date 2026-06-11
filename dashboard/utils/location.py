"""Ключи районов — как в analyze/location_utils.py."""

import pandas as pd


def make_district_key(row) -> str:
    municipality = "" if pd.isna(row.get("Муниципалитет")) else str(row["Муниципалитет"]).strip()
    populated = "" if pd.isna(row.get("Населенный пункт")) else str(row["Населенный пункт"]).strip()

    if municipality and populated:
        return f"{municipality}, {populated}"
    if municipality:
        return f"{municipality} (без указания населённого пункта)"
    if populated:
        return populated
    return "Не указан"
