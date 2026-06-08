import numpy as np
import pandas as pd

def get_kpi_metrics(df):

    total = len(df)

    # проблемные (пример логики)
    if "Проблема" in df.columns:
        problem_count = df["Проблема"].sum()
    else:
        problem_count = total  # fallback

    municipalities = df["Муниципалитет"].nunique()

    avg_severity = df["Серьёзность"].mean()

    return {
        "total": total,
        "problem_count": problem_count,
        "municipalities": municipalities,
        "avg_severity": round(avg_severity, 2)
    }

def get_severity_stats(df):
    """
        Возвращает количество и процент проблем
        по уровням серьёзности.
    """

    high = len(df[df["Серьёзность"].between(4, 5)])
    medium = len(df[df["Серьёзность"].between(2, 3)])
    low = len(df[df["Серьёзность"].between(0, 1)])

    total = high + medium + low

    if total == 0:
        return {
            "high": {"count": 0, "percent": 0},
            "medium": {"count": 0, "percent": 0},
            "low": {"count": 0, "percent": 0},
        }

    return {
        "high": {
            "count": high,
            "percent": round(high / total * 100, 1)
        },
        "medium": {
            "count": medium,
            "percent": round(medium / total * 100, 1)
        },
        "low": {
            "count": low,
            "percent": round(low / total * 100, 1)
        }
    }