import numpy as np
import pandas as pd

from utils.location import make_district_key
from utils.problem import is_problem


def get_kpi_metrics(df, cleaning_stats: dict | None = None):
    analyzed = len(df)
    total_input = cleaning_stats["total_input"] if cleaning_stats else analyzed

    if "Проблема" in df.columns:
        problems = df[df["Проблема"].apply(is_problem)]
        problem_count = len(problems)
        districts_with_problems = (
            int(problems.apply(make_district_key, axis=1).nunique()) if len(problems) else 0
        )
    else:
        problem_count = analyzed
        districts_with_problems = 0

    avg_severity = round(df["Серьёзность"].mean(), 2) if "Серьёзность" in df.columns else 0.0

    return {
        "total": total_input,
        "analyzed": analyzed,
        "problem_count": problem_count,
        "districts_with_problems": districts_with_problems,
        "avg_severity": avg_severity,
        "cleaning_stats": cleaning_stats,
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