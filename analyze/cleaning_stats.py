"""Статистика этапа очистки исходного Excel."""

from __future__ import annotations

import json
from pathlib import Path


def save_cleaning_stats(stats: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def load_cleaning_stats(path: str | Path | None) -> dict | None:
    if not path:
        return None
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
