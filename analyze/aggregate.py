import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from cleaning_stats import load_cleaning_stats
from columns import COL_PROBLEM, COL_SEVERITY, normalize_analysis_columns
from summary_utils import build_district_key_problems
from export_names import KIND_SUMMARY, KIND_SUMMARY_TXT, export_path
from leadership_summary import build_leadership_summary
from location_utils import make_district_key
from pdf_report import generate_leadership_pdf


def parse_args():
    parser = argparse.ArgumentParser(description="Агрегация проблемных районов Top-3 / Top-10")
    parser.add_argument("--input", required=True, help="Excel после LLM-анализа")
    parser.add_argument("--output", default=None, help="Итоговый отчёт Excel")
    parser.add_argument("--summary", default=None, help="PDF-справка для руководства")
    return parser.parse_args()


def build_district_stats(df):
    problems = df[df[COL_PROBLEM] == True].copy()  # noqa: E712
    problems["район"] = problems.apply(make_district_key, axis=1)

    rows = []
    for district, group in problems.groupby("район"):
        severities = group[COL_SEVERITY].fillna(1).astype(int)
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
            "ключевые_проблемы": build_district_key_problems(group),
            "примеры_обращений": " | ".join(str(e)[:200] for e in examples),
        })

    stats = pd.DataFrame(rows)
    if stats.empty:
        return stats

    return stats.sort_values("рейтинг", ascending=False).reset_index(drop=True)


def run_aggregate(input_file, output_file=None, summary_file=None):
    print(f"Загрузка {input_file}")
    df = normalize_analysis_columns(pd.read_excel(input_file))

    stats = build_district_stats(df)
    total_problems = int((df[COL_PROBLEM] == True).sum())  # noqa: E712
    analyzed_count = len(df)
    cleaning = load_cleaning_stats(Path(input_file).parent / "cleaning_stats.json")
    total_input = cleaning["total_input"] if cleaning else analyzed_count

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"report_{timestamp}.xlsx"

    top10 = stats.head(10).copy()
    top3 = stats.head(3).copy()
    if not top10.empty:
        top10.insert(0, "ранг", range(1, len(top10) + 1))
        top3.insert(0, "ранг", range(1, len(top3) + 1))

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        top10.to_excel(writer, sheet_name="Топ-10", index=False)
        top3.to_excel(writer, sheet_name="Топ-3", index=False)
        stats.to_excel(writer, sheet_name="Все районы", index=False)

        avg_severity = (
            round(df[COL_SEVERITY].mean(), 2)
            if COL_SEVERITY in df.columns and analyzed_count
            else 0.0
        )
        overview = pd.DataFrame([{
            "всего_в_файле": total_input,
            "отобрано_к_анализу": analyzed_count,
            "выявлено_проблем": total_problems,
            "районов_с_проблемами": len(stats),
            "средняя_тяжесть": avg_severity,
            "доля_проблем_%": round(total_problems / analyzed_count * 100, 1) if analyzed_count else 0,
        }])
        overview.to_excel(writer, sheet_name="Обзор", index=False)

    print(f"Отчёт: {output_file}")

    if summary_file is None:
        summary_file = export_path(Path(output_file).parent, KIND_SUMMARY)

    text_summary = build_leadership_summary(
        stats, analyzed_count, total_problems, total_input,
    )
    txt_path = export_path(Path(output_file).parent, KIND_SUMMARY_TXT)
    txt_path.write_text(text_summary, encoding="utf-8")
    print(f"Сводка (TXT): {txt_path}")

    generate_leadership_pdf(
        stats,
        analyzed_count,
        total_problems,
        summary_file,
        total_input=total_input,
        avg_severity=avg_severity,
    )
    print(f"Справка (PDF): {summary_file}")
    print()
    print(text_summary)

    return output_file, summary_file


def main():
    args = parse_args()
    run_aggregate(args.input, args.output, args.summary)


if __name__ == "__main__":
    main()
