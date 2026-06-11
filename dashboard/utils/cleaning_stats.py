import json

from core.report_files import KIND_CLEANING_STATS, find_report_file


def load_cleaning_stats() -> dict | None:
    path = find_report_file(KIND_CLEANING_STATS)
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None
