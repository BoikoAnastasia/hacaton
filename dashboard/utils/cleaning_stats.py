import json

from core.config import DATA_FILE_CLEANING_STATS


def load_cleaning_stats() -> dict | None:
    if not DATA_FILE_CLEANING_STATS.exists():
        return None
    return json.loads(DATA_FILE_CLEANING_STATS.read_text(encoding="utf-8"))
