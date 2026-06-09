import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

from columns import COL_PROBLEM, COL_SEVERITY, COL_SUMMARY, normalize_analysis_columns
from location_utils import make_district_key


def parse_args():
    parser = argparse.ArgumentParser(description="Агрегация проблемных районов Top-3 / Top-10")
    parser.add_argument("--input", required=True, help="Excel после LLM-анализа")
    parser.add_argument("--output", default=None, help="Итоговый отчёт Excel")
    parser.add_argument("--summary", default=None, help="Текстовая справка для руководства")
    return parser.parse_args()


def build_district_stats(df):
    problems = df[df[COL_PROBLEM] == True].copy()  # noqa: E712
    problems["район"] = problems.apply(make_district_key, axis=1)

    rows = []
    for district, group in problems.groupby("район"):
        severities = group[COL_SEVERITY].fillna(1).astype(int)
        summaries = group[COL_SUMMARY].dropna().astype(str)
        summary_counts = Counter(
            s for s in summaries
            if s and s.lower() not in ("ошибка парсинга", "ошибка генерации")
        )

        top_issues = [text for text, _ in summary_counts.most_common(5)]
        examples = []
        for col in ("Очищенный текст", "clean_text", "Текст инцидента"):
            if col in group.columns:
                examples = group[col].dropna().head(3).tolist()
                if examples:
                    break

        rows.append({
            "район": district,
            "муниципалитет": group["Муниципалитет"].iloc[0] if "Муниципалитет" in group.columns else "",
            "населенный_пункт": group["Населенный пункт"].iloc[0] if "Населенный пункт" in group.columns else "",
            "количество_проблем": len(group),
            "сумма_тяжести": int(severities.sum()),
            "средняя_тяжесть": round(severities.mean(), 2),
            "рейтинг": int(severities.sum() + len(group)),
            "ключевые_проблемы": "; ".join(top_issues),
            "примеры_обращений": " | ".join(str(e)[:200] for e in examples),
        })

    stats = pd.DataFrame(rows)
    if stats.empty:
        return stats

    return stats.sort_values("рейтинг", ascending=False).reset_index(drop=True)


def build_leadership_summary(stats, total_rows, total_problems):
    if stats.empty:
        return "Проблемных обращений не выявлено."

    lines = [
        "СПРАВКА ПО ПРОБЛЕМНЫМ РАЙОНАМ",
        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        "",
        f"Проанализировано обращений: {total_rows}",
        f"Выявлено проблем: {total_problems}",
        "",
        "ТОП-3 ПРОБЛЕМНЫХ РАЙОНА:",
    ]

    for _, row in stats.head(3).iterrows():
        lines.append(
            f"\n{row['район']}: {row['количество_проблем']} проблем, "
            f"суммарная тяжесть {row['сумма_тяжести']}. "
            f"Основные причины: {row['ключевые_проблемы']}"
        )

    lines.extend(["", "ТОП-10 (кратко):"])
    for i, row in stats.head(10).iterrows():
        lines.append(f"{i + 1}. {row['район']} — {row['количество_проблем']} проблем")

    return "\n".join(lines)


def run_aggregate(input_file, output_file=None, summary_file=None):
    print(f"Загрузка {input_file}")
    df = normalize_analysis_columns(pd.read_excel(input_file))

    stats = build_district_stats(df)
    total_problems = int((df[COL_PROBLEM] == True).sum())  # noqa: E712

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"report_{timestamp}.xlsx"

    top10 = stats.head(10).copy()
    top3 = stats.head(3).copy()
    if not top10.empty:
        top10.insert(0, "ранг", range(1, len(top10) + 1))
        top3.insert(0, "ранг", range(1, len(top3) + 1))

    text_summary = build_leadership_summary(stats, len(df), total_problems)

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        top10.to_excel(writer, sheet_name="Топ-10", index=False)
        top3.to_excel(writer, sheet_name="Топ-3", index=False)
        stats.to_excel(writer, sheet_name="Все районы", index=False)

        overview = pd.DataFrame([{
            "всего_обращений": len(df),
            "выявлено_проблем": total_problems,
            "районов_с_проблемами": len(stats),
            "доля_проблем_%": round(total_problems / len(df) * 100, 1) if len(df) else 0,
        }])
        overview.to_excel(writer, sheet_name="Обзор", index=False)

    print(f"Отчёт: {output_file}")

    if summary_file is None:
        summary_file = Path(output_file).with_suffix(".txt")

    Path(summary_file).write_text(text_summary, encoding="utf-8")
    print(f"Справка: {summary_file}")
    print()
    print(text_summary)

    return output_file, summary_file


def main():
    args = parse_args()
    run_aggregate(args.input, args.output, args.summary)


if __name__ == "__main__":
    main()
