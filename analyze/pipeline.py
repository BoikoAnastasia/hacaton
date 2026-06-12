"""
Полный пайплайн ГородОК:
  1. excel.py           — очистка и фильтрация
  2. анализ             — fast / cluster / llm / hybrid
  3. aggregate.py       — Top-3 / Top-10, PDF, TXT-сводка
  4. summarize_top.py   — LLM-описание топ-районов (только hybrid)

Документация: docs/РЕЖИМЫ_ОБРАБОТКИ.md
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from report_paths import ensure_report_dir, plan_report_dir, remove_if_empty, report_files

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Полный пайплайн анализа обращений")
    parser.add_argument("--input", default=None, help="Исходный Excel (не нужен при --skip-clean --cleaned)")
    parser.add_argument("--work-dir", default=str(ROOT_DIR), help="Рабочая директория")
    parser.add_argument("--limit", type=int, default=0, help="Ограничить строки (0 = все)")
    parser.add_argument("--random", action="store_true", help="Случайная выборка при --limit")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--output-dir", default=None, help="Папка для результатов (по умолчанию «Отчет от …»)")
    parser.add_argument("--skip-clean", action="store_true", help="Пропустить очистку")
    parser.add_argument("--skip-llm", action="store_true", help="Пропустить LLM (только отчёт)")
    parser.add_argument("--cleaned", default=None, help="Готовый cleaned.xlsx (если --skip-clean)")
    parser.add_argument("--analyzed", default=None, help="Готовый result.xlsx (если --skip-llm)")
    parser.add_argument(
        "--mode",
        choices=["cluster", "llm", "fast", "hybrid"],
        default="cluster",
        help="cluster=эмбеддинги+LLM на представителях (~45-60 мин), llm=каждая строка (~5 суток), fast=правила (низкое качество)",
    )
    parser.add_argument("--clusters", type=int, default=800, help="Верхний предел кластеров для mode=cluster")
    parser.add_argument(
        "--turbo",
        action="store_true",
        help="Быстрый LLM: ~800 вызовов max, summary из темы, batch 8 (~10-25 мин на 400k)",
    )
    return parser.parse_args()


def child_env():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8:replace"
    env["PYTHONUTF8"] = "1"
    env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    env["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
    env["TQDM_DISABLE"] = "1"
    return env


def run_step(cmd, cwd):
    print(f"\n{'=' * 60}")
    line = " ".join(str(c) for c in cmd)
    sys.stdout.buffer.write((line + "\n").encode("utf-8", errors="replace"))
    print("=" * 60)
    result = subprocess.run(cmd, cwd=cwd, env=child_env())
    if result.returncode != 0:
        sys.exit(result.returncode)


def apply_row_limit(cleaned_path: str, limit: int, random_sample: bool) -> str:
    if limit <= 0:
        return cleaned_path

    df = pd.read_excel(cleaned_path)
    total = len(df)
    n = min(limit, total)
    if random_sample:
        df = df.sample(n=n, random_state=42)
        print(f"Случайная выборка: {n} из {total} строк")
    else:
        df = df.head(n)
        print(f"Взяты первые {n} строк")

    sampled = str(Path(cleaned_path).with_name("cleaned_sample.xlsx"))
    df.to_excel(sampled, index=False)
    return sampled


def main():
    args = parse_args()
    cwd = Path(args.work_dir)
    python = sys.executable

    report_dir = Path(args.output_dir) if args.output_dir else plan_report_dir(cwd)
    paths = report_files(report_dir)
    report_dir_created = False

    def activate_report_dir():
        nonlocal report_dir_created
        if not report_dir_created:
            ensure_report_dir(report_dir)
            report_dir_created = True
            print(f"\nПапка отчёта: {report_dir}\n")

    try:
        cleaned = args.cleaned or str(paths["cleaned"])
        analyzed = args.analyzed or str(paths["result"])
        report = str(paths["report"])

        if not args.skip_clean:
            if not args.input:
                print("Укажите --input для очистки или используйте --skip-clean --cleaned")
                sys.exit(1)
            activate_report_dir()
            run_step([
                python,
                str(SCRIPT_DIR / "excel.py"),
                "--input", args.input,
                "--output", cleaned,
            ], cwd)
        else:
            if not args.cleaned:
                cleaned = str(paths["cleaned"])
            if not Path(cleaned).exists():
                print(f"Файл не найден: {cleaned}")
                sys.exit(1)
            activate_report_dir()

        cleaned = apply_row_limit(cleaned, args.limit, args.random)

        if args.skip_llm:
            analyzed = args.analyzed
            if not analyzed or not Path(analyzed).exists():
                print("Укажите --analyzed для пропуска анализа")
                sys.exit(1)
        elif args.mode == "cluster":
            cluster_cmd = [
                python, "-u",
                str(SCRIPT_DIR / "cluster_analyze.py"),
                "--input", cleaned,
                "--output", analyzed,
                "--clusters", str(args.clusters),
                "--batch-size", str(args.batch_size),
            ]
            if args.turbo:
                cluster_cmd.append("--turbo")
            run_step(cluster_cmd, cwd)
        elif args.mode == "fast":
            run_step([
                python,
                str(SCRIPT_DIR / "fast_analyze.py"),
                "--input", cleaned,
                "--output", analyzed,
            ], cwd)
        elif args.mode == "llm":
            llm_cmd = [
                python, "-u",
                str(SCRIPT_DIR / "test_qwen.py"),
                "--input", cleaned,
                "--output", analyzed,
                "--batch-size", str(args.batch_size),
            ]
            run_step(llm_cmd, cwd)
        else:
            run_step([
                python,
                str(SCRIPT_DIR / "fast_analyze.py"),
                "--input", cleaned,
                "--output", analyzed,
            ], cwd)

        run_step([
            python,
            str(SCRIPT_DIR / "aggregate.py"),
            "--input", analyzed,
            "--output", report,
            "--summary", str(paths["summary"]),
        ], cwd)

        if args.mode == "hybrid" and not args.skip_llm:
            run_step([
                python,
                str(SCRIPT_DIR / "summarize_top.py"),
                "--input", analyzed,
                "--report", report,
                "--output", report,
            ], cwd)

        print(f"\n{'=' * 60}")
        print("ПАЙПЛАЙН ЗАВЕРШЁН")
        print(f"  Папка:            {report_dir}")
        print(f"  Очищенные данные: {cleaned}")
        print(f"  Анализ:           {analyzed}")
        print(f"  Отчёт:            {report}")
        print(f"  Справка:          {paths['summary']}")
        print("=" * 60)
    except SystemExit as exc:
        if exc.code not in (0, None) and remove_if_empty(report_dir):
            print(f"Пустая папка удалена: {report_dir}")
        raise
    except Exception:
        if remove_if_empty(report_dir):
            print(f"Пустая папка удалена: {report_dir}")
        raise


if __name__ == "__main__":
    main()
