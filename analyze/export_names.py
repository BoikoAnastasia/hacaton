"""Человекочитаемые имена файлов отчёта внутри папки «Отчет от …»."""

from __future__ import annotations

from pathlib import Path

KIND_RESULT = "result"
KIND_REPORT = "report"
KIND_SUMMARY = "summary"
KIND_CLEANED = "cleaned"
KIND_CLEANING_STATS = "cleaning_stats"
KIND_SUMMARY_TXT = "summary_txt"

LABELS: dict[str, str] = {
    KIND_RESULT: "полный анализ",
    KIND_REPORT: "топ районов",
    KIND_SUMMARY: "справка",
    KIND_SUMMARY_TXT: "сводка",
    KIND_CLEANED: "очищенные данные",
}

LEGACY_FILENAMES: dict[str, str] = {
    KIND_RESULT: "result.xlsx",
    KIND_REPORT: "report.xlsx",
    KIND_SUMMARY: "report.pdf",
    KIND_SUMMARY_TXT: "report.txt",
    KIND_CLEANED: "cleaned.xlsx",
    KIND_CLEANING_STATS: "cleaning_stats.json",
}

DOWNLOAD_KINDS = (KIND_RESULT, KIND_REPORT, KIND_SUMMARY)


def export_filename(report_dir_name: str, kind: str) -> str:
    """Имя файла: «Отчет от … — полный анализ.xlsx»."""
    return f"{report_dir_name} — {LABELS[kind]}{Path(LEGACY_FILENAMES[kind]).suffix}"


def export_path(report_dir: Path, kind: str) -> Path:
    return Path(report_dir) / export_filename(Path(report_dir).name, kind)


def resolve_export_file(report_dir: Path, kind: str) -> Path | None:
    """Новое имя или legacy (старые отчёты)."""
    report_dir = Path(report_dir)
    if kind in LABELS:
        preferred = export_path(report_dir, kind)
        if preferred.exists():
            return preferred
    legacy_name = LEGACY_FILENAMES.get(kind)
    if not legacy_name:
        return None
    legacy = report_dir / legacy_name
    if legacy.exists():
        return legacy
    return None


def zip_archive_name(report_dir_name: str) -> str:
    return f"{report_dir_name} — файлы отчёта.zip"
