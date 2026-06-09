import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from columns import (
    COL_PROBLEM,
    COL_SEVERITY,
    COL_SUMMARY,
    RESULT_COLUMNS,
    attach_severity_labels,
    select_columns,
)
from llm_utils import analyze_batch, load_model
from problem_utils import refine_problem
from severity_utils import refine_severity
from summary_utils import make_summary_from_row, merge_llm_summary

TEXT_COLUMNS = ("Очищенный текст", "clean_text")
CHECKPOINT_EVERY = 50


def parse_args():
    parser = argparse.ArgumentParser(description="LLM-анализ обращений граждан (полный прогон)")
    parser.add_argument("--input", default="cleaned.xlsx")
    parser.add_argument("--output", default=None)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--checkpoint-every", type=int, default=CHECKPOINT_EVERY)
    parser.add_argument("--resume", default=None)
    return parser.parse_args()


def detect_text_column(df):
    for col in TEXT_COLUMNS:
        if col in df.columns:
            return col
    raise KeyError(f"Нет колонки с текстом: {list(df.columns)}")


def get_meta_columns(df):
    theme = "Тема" if "Тема" in df.columns else None
    group = "Группа тем" if "Группа тем" in df.columns else None
    return theme, group


def save_checkpoint(df, path):
    df.to_excel(path, index=False)
    print(f"Чекпоинт: {path}")


def run_analysis(args):
    if args.resume:
        print(f"Продолжение с {args.resume}")
        df = pd.read_excel(args.resume)
        for col in (COL_PROBLEM, COL_SEVERITY, COL_SUMMARY):
            if col not in df.columns:
                df[col] = None
        start_idx = df[COL_PROBLEM].notna().sum()
    else:
        print(f"Загрузка {args.input}")
        df = pd.read_excel(args.input)
        if args.limit > 0:
            df = df.head(args.limit).copy()
        df[COL_PROBLEM] = None
        df[COL_SEVERITY] = None
        df[COL_SUMMARY] = None
        start_idx = 0

    text_col = detect_text_column(df)
    theme_col, group_col = get_meta_columns(df)
    texts = df[text_col].tolist()

    if start_idx >= len(texts):
        print("Все строки уже обработаны")
        return df

    tokenizer, model = load_model()
    checkpoint_path = Path(args.output or "result_checkpoint.xlsx").with_name(
        Path(args.output or "result_checkpoint.xlsx").stem + "_checkpoint.xlsx"
    )

    for i in range(start_idx, len(texts), args.batch_size):
        end = min(i + args.batch_size, len(texts))
        batch_df = df.iloc[i:end]

        print(f"Батч {i}-{end} / {len(texts)}")
        results = analyze_batch(
            batch_df[text_col].tolist(),
            batch_df[theme_col].tolist() if theme_col else None,
            batch_df[group_col].tolist() if group_col else None,
            tokenizer,
            model,
        )

        for j, (problem, severity, summary) in enumerate(results):
            row_idx = i + j
            row = df.iloc[row_idx]
            text = row[text_col]
            is_problem = refine_problem(
                problem, text, row.get("Тема"), row.get("Группа тем"),
            )
            severity = refine_severity(
                severity, text, row.get("Тема"), row.get("Группа тем"), is_problem=is_problem,
            )
            rule_summary = make_summary_from_row(row, text, is_problem)
            summary = merge_llm_summary(rule_summary, summary)
            df.loc[row_idx, COL_PROBLEM] = is_problem
            df.loc[row_idx, COL_SEVERITY] = severity
            df.loc[row_idx, COL_SUMMARY] = summary

        if ((i - start_idx) // args.batch_size + 1) % args.checkpoint_every == 0:
            save_checkpoint(df, checkpoint_path)

    return df


def main():
    args = parse_args()
    if args.output is None:
        args.output = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    df = run_analysis(args)
    select_columns(attach_severity_labels(df), RESULT_COLUMNS).to_excel(args.output, index=False)

    problems = df[COL_PROBLEM].eq(True).sum()
    print(f"Готово: {args.output}, проблем: {problems}/{len(df)}")


if __name__ == "__main__":
    main()
