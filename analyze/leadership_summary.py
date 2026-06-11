"""Текстовая краткая сводка для руководства (как в report.txt)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd


def build_leadership_summary(
    stats: pd.DataFrame,
    total_rows: int,
    total_problems: int,
    total_input: int | None = None,
    generated_at: datetime | None = None,
) -> str:
    when = generated_at or datetime.now()

    if stats.empty:
        return "Проблемных обращений не выявлено."

    lines = [
        "СПРАВКА ПО ПРОБЛЕМНЫМ РАЙОНАМ",
        f"Дата: {when.strftime('%d.%m.%Y %H:%M')}",
        "",
    ]
    if total_input and total_input != total_rows:
        lines.extend([
            f"Всего в исходном файле: {total_input}",
            f"Отобрано к анализу (открытые решаемые): {total_rows}",
        ])
    else:
        lines.append(f"Проанализировано обращений: {total_rows}")
    lines.extend([
        f"Выявлено проблем: {total_problems}",
        f"Районов с проблемами: {len(stats)}",
        "",
        "ТОП-3 ПРОБЛЕМНЫХ РАЙОНА:",
    ])

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
