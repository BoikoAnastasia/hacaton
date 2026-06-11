"""Поиск файлов отчёта (новые и legacy-имена)."""

from __future__ import annotations

from pathlib import Path

from core.config import REPORTS_DIR
from core.export_names_bridge import (
    DOWNLOAD_KINDS,
    KIND_CLEANED,
    KIND_CLEANING_STATS,
    KIND_REPORT,
    KIND_RESULT,
    KIND_SUMMARY,
    KIND_SUMMARY_TXT,
    LEGACY_FILENAMES,
    export_filename,
    resolve_export_file,
    zip_archive_name,
)
from core.report_context import get_active_report_dir

ZIP_EXTRA_KINDS = (KIND_SUMMARY_TXT,)

__all__ = [
    "DOWNLOAD_KINDS",
    "KIND_CLEANED",
    "KIND_REPORT",
    "KIND_RESULT",
    "KIND_SUMMARY",
    "KIND_SUMMARY_TXT",
    "ZIP_EXTRA_KINDS",
    "download_filename",
    "find_report_file",
    "zip_download_name",
]


def find_report_file(kind: str) -> Path | None:
    active = get_active_report_dir()
    if active:
        found = resolve_export_file(active, kind)
        if found:
            return found
    legacy_name = LEGACY_FILENAMES.get(kind)
    if not legacy_name:
        return None
    fallback = REPORTS_DIR / legacy_name
    return fallback if fallback.exists() else None


def download_filename(kind: str) -> str:
    active = get_active_report_dir()
    if active:
        return export_filename(active.name, kind)
    return LEGACY_FILENAMES[kind]


def zip_download_name() -> str:
    active = get_active_report_dir()
    if active:
        return zip_archive_name(active.name)
    return "ГородОК — файлы отчёта.zip"
