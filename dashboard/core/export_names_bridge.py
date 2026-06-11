"""Импорт имён файлов отчёта из analyze/export_names (с fallback для старых версий)."""

from __future__ import annotations

import sys

from core.config import ANALYZE_DIR

_analyze = str(ANALYZE_DIR)
if _analyze not in sys.path:
    sys.path.insert(0, _analyze)

import export_names as _en  # noqa: E402

KIND_RESULT = _en.KIND_RESULT
KIND_REPORT = _en.KIND_REPORT
KIND_SUMMARY = _en.KIND_SUMMARY
KIND_CLEANED = _en.KIND_CLEANED
KIND_CLEANING_STATS = _en.KIND_CLEANING_STATS
KIND_SUMMARY_TXT = getattr(_en, "KIND_SUMMARY_TXT", "summary_txt")

DOWNLOAD_KINDS = _en.DOWNLOAD_KINDS
LEGACY_FILENAMES = dict(_en.LEGACY_FILENAMES)
if KIND_SUMMARY_TXT not in LEGACY_FILENAMES:
    LEGACY_FILENAMES[KIND_SUMMARY_TXT] = "report.txt"

LABELS = dict(getattr(_en, "LABELS", {}))
if KIND_SUMMARY_TXT not in LABELS:
    LABELS[KIND_SUMMARY_TXT] = "сводка"

zip_archive_name = _en.zip_archive_name


def export_filename(report_dir_name: str, kind: str) -> str:
    if kind in getattr(_en, "LABELS", {}) and kind in _en.LEGACY_FILENAMES:
        return _en.export_filename(report_dir_name, kind)
    if kind == KIND_SUMMARY_TXT:
        return f"{report_dir_name} — {LABELS[KIND_SUMMARY_TXT]}.txt"
    raise KeyError(kind)


def export_path(report_dir, kind: str):
    from pathlib import Path

    return Path(report_dir) / export_filename(Path(report_dir).name, kind)


def resolve_export_file(report_dir, kind: str):
    found = _en.resolve_export_file(report_dir, kind)
    if found or kind != KIND_SUMMARY_TXT:
        return found
    report_dir = __import__("pathlib").Path(report_dir)
    legacy = report_dir / LEGACY_FILENAMES[KIND_SUMMARY_TXT]
    return legacy if legacy.exists() else None
