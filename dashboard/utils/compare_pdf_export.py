"""Экспорт сравнения отчётов в PDF."""

from __future__ import annotations

import sys

import pandas as pd

from core.config import ANALYZE_DIR

sys.path.insert(0, str(ANALYZE_DIR))
from compare_pdf import comparison_pdf_filename, generate_comparison_pdf  # noqa: E402


def build_comparison_pdf(first, second, districts: pd.DataFrame) -> tuple[bytes, str]:
    pdf_bytes = generate_comparison_pdf(first, second, districts)
    filename = comparison_pdf_filename(first.label, second.label)
    return pdf_bytes, filename
