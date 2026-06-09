"""Ключи районов для отчётов."""

import pandas as pd

MUNICIPALITY_COL = "Муниципалитет"
POPULATED_COL = "Населенный пункт"


def _location_part(row, col: str) -> str:
    val = row.get(col)
    if pd.isna(val):
        return ""
    return str(val).strip()


def make_district_key(row) -> str:
    """
    Ключ района для группировки в отчёте.
    Если населённый пункт не указан — явно помечаем это в названии.
    """
    municipality = _location_part(row, MUNICIPALITY_COL)
    populated = _location_part(row, POPULATED_COL)

    if municipality and populated:
        return f"{municipality}, {populated}"
    if municipality:
        return f"{municipality} (без указания населённого пункта)"
    if populated:
        return populated
    return "Не указан"
