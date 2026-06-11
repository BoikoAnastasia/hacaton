from pathlib import Path

# gorodok/dashboard/core/config.py → gorodok/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = DASHBOARD_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
REPORTS_DIR = DATA_DIR / "reports"

DATA_FILE_TOP_10 = REPORTS_DIR / "report.xlsx"
DATA_FILE_RESULT = REPORTS_DIR / "result.xlsx"
DATA_FILE_SUMMARY = REPORTS_DIR / "report.pdf"
DATA_FILE_CLEANING_STATS = REPORTS_DIR / "cleaning_stats.json"

ANALYZE_DIR = PROJECT_ROOT / "analyze"


def resolve_python() -> Path:
    """Локальный .venv / qwen_env в проекте или qwen_env в родительской папке."""
    for candidate in (
        PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
        PROJECT_ROOT / "qwen_env" / "Scripts" / "python.exe",
        PROJECT_ROOT.parent / "qwen_env" / "Scripts" / "python.exe",
    ):
        if candidate.exists():
            return candidate
    return PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"


VENV_PYTHON = resolve_python()
