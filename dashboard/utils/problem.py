import pandas as pd


def is_problem(value) -> bool:
    if value is True or value == 1:
        return True
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().upper() in ("ИСТИНА", "TRUE", "1", "ДА")
    return bool(value)


def filter_problems(df):
    if df is None or "Проблема" not in df.columns:
        return df
    return df[df["Проблема"].apply(is_problem)].copy()
