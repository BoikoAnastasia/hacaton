"""Список и активация папок «Отчет от …» из storage/output."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from core.config import OUTPUT_REPORTS_ROOT, REPORTS_DIR
from core.export_names_bridge import (
    KIND_CLEANED,
    KIND_CLEANING_STATS,
    KIND_REPORT,
    KIND_RESULT,
    KIND_SUMMARY,
    KIND_SUMMARY_TXT,
    resolve_export_file,
)

OPEN_KINDS = (KIND_RESULT, KIND_REPORT)
CACHE_KINDS = (
    KIND_RESULT,
    KIND_REPORT,
    KIND_SUMMARY,
    KIND_SUMMARY_TXT,
    KIND_CLEANED,
    KIND_CLEANING_STATS,
)


@dataclass(frozen=True)
class SavedReport:
    path: Path
    label: str
    mtime: float

    @property
    def has_result(self) -> bool:
        return resolve_export_file(self.path, KIND_RESULT) is not None


def list_saved_reports() -> list[SavedReport]:
    if not OUTPUT_REPORTS_ROOT.is_dir():
        return []

    entries: list[SavedReport] = []
    for folder in OUTPUT_REPORTS_ROOT.iterdir():
        if not folder.is_dir() or not folder.name.startswith("Отчет от"):
            continue
        if not any(resolve_export_file(folder, kind) for kind in OPEN_KINDS):
            continue
        entries.append(SavedReport(
            path=folder,
            label=folder.name,
            mtime=folder.stat().st_mtime,
        ))

    entries.sort(key=lambda item: item.mtime, reverse=True)
    return entries


def can_open_report(report_dir: str | Path) -> bool:
    folder = Path(report_dir).resolve()
    if not folder.is_dir():
        return False
    return any(resolve_export_file(folder, kind) for kind in OPEN_KINDS)


def sync_report_cache(report_dir: Path) -> bool:
    """Копия в dashboard/data/reports — для совместимости, не для UI."""
    report_dir = Path(report_dir).resolve()
    if not can_open_report(report_dir):
        return False

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    for existing in REPORTS_DIR.iterdir():
        if existing.is_file():
            existing.unlink()

    copied = False
    for kind in CACHE_KINDS:
        src = resolve_export_file(report_dir, kind)
        if src:
            shutil.copy2(src, REPORTS_DIR / src.name)
            copied = True
    return copied
