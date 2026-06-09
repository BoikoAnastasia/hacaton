"""
Быстрый анализ без LLM: ~300k строк за 1-3 минуты.
Правила + ключевые слова. LLM не нужен для каждой строки.
"""

import argparse
import time
from datetime import datetime

import pandas as pd

from columns import (
    COL_PROBLEM,
    COL_SEVERITY,
    COL_SUMMARY,
    RESULT_COLUMNS,
    attach_severity_labels,
    select_columns,
)
from problem_utils import refine_problem
from severity_utils import refine_severity
from summary_utils import make_summary_from_row

TEXT_COLUMNS = ("Очищенный текст", "clean_text")


def parse_args():
    parser = argparse.ArgumentParser(description="Быстрый rule-based анализ обращений")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def detect_text_column(df):
    for col in TEXT_COLUMNS:
        if col in df.columns:
            return col
    raise KeyError(f"Нет колонки с текстом: {list(df.columns)}")


def detect_problem(row, text, incident_type):
    if not text:
        return False, 0, "Пустое обращение"

    theme = row.get("Тема")
    group = row.get("Группа тем")
    is_problem = refine_problem(True, text, theme, group)
    severity = refine_severity(None, text, theme, group, is_problem=is_problem)
    return is_problem, severity, make_summary_from_row(row, text, is_problem)


def analyze_dataframe(df):
    text_col = detect_text_column(df)
    type_col = "Тип инцидента" if "Тип инцидента" in df.columns else None

    problems, severities, summaries = [], [], []

    texts = df[text_col].fillna("").astype(str)
    types = df[type_col].fillna("Решаемый") if type_col else pd.Series(["Решаемый"] * len(df))

    for idx, (text, itype) in enumerate(zip(texts, types)):
        p, s, sm = detect_problem(df.iloc[idx], text, itype)
        problems.append(p)
        severities.append(s)
        summaries.append(sm)

    df = df.copy()
    df[COL_PROBLEM] = problems
    df[COL_SEVERITY] = severities
    df[COL_SUMMARY] = summaries
    return df


def main():
    args = parse_args()
    t0 = time.time()

    print(f"Загрузка {args.input}...")
    df = pd.read_excel(args.input)
    print(f"Строк: {len(df)}")

    df = analyze_dataframe(df)

    elapsed = time.time() - t0
    problems = sum(df[COL_PROBLEM])
    print(f"Готово за {elapsed:.1f}с ({len(df)/elapsed:.0f} стр/с)")
    print(f"Проблем: {problems} ({problems/len(df)*100:.1f}%)")

    output = args.output or f"result_fast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    select_columns(attach_severity_labels(df), RESULT_COLUMNS).to_excel(output, index=False)
    print(f"Сохранено: {output}")


if __name__ == "__main__":
    main()
