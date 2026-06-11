"""Загрузка краткой текстовой сводки для страницы «Отчёты»."""

from __future__ import annotations

import sys

import pandas as pd

from core.config import ANALYZE_DIR
from core.report_files import KIND_REPORT, KIND_SUMMARY_TXT, find_report_file

sys.path.insert(0, str(ANALYZE_DIR))
from leadership_summary import build_leadership_summary  # noqa: E402


def load_leadership_summary_text() -> str | None:
    txt_path = find_report_file(KIND_SUMMARY_TXT)
    if txt_path and txt_path.exists():
        return txt_path.read_text(encoding="utf-8")

    report_path = find_report_file(KIND_REPORT)
    if not report_path or not report_path.exists():
        return None

    try:
        overview = pd.read_excel(report_path, sheet_name="Обзор")
        all_districts = pd.read_excel(report_path, sheet_name="Все районы")
    except (ValueError, OSError):
        return None

    if overview.empty or all_districts.empty:
        return None

    row = overview.iloc[0]
    if "отобрано_к_анализу" in overview.columns:
        total_rows = int(row["отобрано_к_анализу"])
        total_input = int(row["всего_в_файле"])
    else:
        total_rows = int(row.get("всего_обращений", 0))
        total_input = None
    total_problems = int(row["выявлено_проблем"])

    return build_leadership_summary(
        all_districts, total_rows, total_problems, total_input,
    )
