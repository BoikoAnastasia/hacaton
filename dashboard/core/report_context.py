"""Пути к файлам активного отчёта «Отчет от …»."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.config import REPORTS_DIR


def normalize_report_path(path: str | Path | None) -> Path | None:
    if not path:
        return None
    folder = Path(path)
    if folder.is_dir():
        return folder.resolve()
    return None


def get_active_report_dir() -> Path | None:
    return normalize_report_path(st.session_state.get("active_report_path"))


def paths_equal(a: str | Path | None, b: str | Path | None) -> bool:
    pa = normalize_report_path(a)
    pb = normalize_report_path(b)
    return pa is not None and pa == pb


def report_path(filename: str) -> Path:
    active = get_active_report_dir()
    if active:
        direct = active / filename
        if direct.exists():
            return direct
    return REPORTS_DIR / filename
