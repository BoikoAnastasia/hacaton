"""Загрузка и сравнение двух отчётов «Отчет от …»."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from core.export_names_bridge import KIND_REPORT, resolve_export_file


@dataclass(frozen=True)
class ReportSnapshot:
    label: str
    path: Path
    total_in_file: int
    analyzed: int
    problems: int
    districts_with_problems: int
    avg_severity: float
    problem_share_pct: float


def _overview_row(overview: pd.DataFrame) -> pd.Series:
    if overview.empty:
        raise ValueError("Лист «Обзор» пуст")
    return overview.iloc[0]


def load_report_snapshot(report_dir: Path) -> ReportSnapshot | None:
    report_dir = Path(report_dir)
    report_path = resolve_export_file(report_dir, KIND_REPORT)
    if not report_path or not report_path.exists():
        return None

    try:
        overview = pd.read_excel(report_path, sheet_name="Обзор")
        row = _overview_row(overview)
    except (ValueError, OSError):
        return None

    if "отобрано_к_анализу" in overview.columns:
        analyzed = int(row["отобрано_к_анализу"])
        total_in_file = int(row["всего_в_файле"])
    else:
        analyzed = int(row.get("всего_обращений", 0))
        total_in_file = analyzed

    return ReportSnapshot(
        label=report_dir.name,
        path=report_dir,
        total_in_file=total_in_file,
        analyzed=analyzed,
        problems=int(row["выявлено_проблем"]),
        districts_with_problems=int(row["районов_с_проблемами"]),
        avg_severity=float(row.get("средняя_тяжесть", 0) or 0),
        problem_share_pct=float(row.get("доля_проблем_%", 0) or 0),
    )


def load_districts(report_dir: Path) -> pd.DataFrame | None:
    report_path = resolve_export_file(Path(report_dir), KIND_REPORT)
    if not report_path or not report_path.exists():
        return None
    try:
        df = pd.read_excel(report_path, sheet_name="Все районы")
    except (ValueError, OSError):
        return None
    if df.empty or "район" not in df.columns:
        return None
    return df


def pct_change(first: float, second: float) -> float | None:
    if first == 0:
        if second == 0:
            return 0.0
        return None
    return round((second - first) / first * 100, 1)


def format_delta(delta: float, *, is_float: bool = False) -> str:
    if is_float:
        return f"{delta:+.2f}"
    return f"{delta:+,.0f}".replace(",", " ")


def format_pct(pct: float | None) -> str:
    if pct is None:
        return "н/д"
    return f"{pct:+.1f}%"


def compare_districts(base: pd.DataFrame, other: pd.DataFrame) -> pd.DataFrame:
    left = base[["район", "количество_проблем", "средняя_тяжесть"]].copy()
    left = left.rename(columns={
        "количество_проблем": "проблем_1",
        "средняя_тяжесть": "тяжесть_1",
    })

    right = other[["район", "количество_проблем", "средняя_тяжесть"]].copy()
    right = right.rename(columns={
        "количество_проблем": "проблем_2",
        "средняя_тяжесть": "тяжесть_2",
    })

    merged = left.merge(right, on="район", how="outer")
    for col in ("проблем_1", "проблем_2", "тяжесть_1", "тяжесть_2"):
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)

    merged["Δ проблем"] = merged["проблем_2"] - merged["проблем_1"]
    merged["Δ проблем, %"] = merged.apply(
        lambda r: pct_change(r["проблем_1"], r["проблем_2"]),
        axis=1,
    )
    merged["Δ тяжести"] = (merged["тяжесть_2"] - merged["тяжесть_1"]).round(2)
    merged["Δ тяжести, %"] = merged.apply(
        lambda r: pct_change(r["тяжесть_1"], r["тяжесть_2"]) if r["тяжесть_1"] > 0 else None,
        axis=1,
    )

    merged["|Δ проблем|"] = merged["Δ проблем"].abs()
    return merged.sort_values("|Δ проблем|", ascending=False).drop(columns=["|Δ проблем|"])


def comparison_warning(base: ReportSnapshot, other: ReportSnapshot) -> str | None:
    if base.analyzed == other.analyzed:
        return None
    return (
        f"Разный объём анализа: **{base.analyzed:,}** vs **{other.analyzed:,}** "
        "отобранных обращений — сравнение ориентировочное."
    ).replace(",", " ")
