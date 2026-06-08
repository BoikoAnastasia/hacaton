from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

REPORTS_DIR = BASE_DIR / "reports"

DATA_FILE_TOP_10 = REPORTS_DIR / "report.xlsx"
DATA_FILE_RESULT = REPORTS_DIR / "result.xlsx"
DATA_FILE_SUMMARY = REPORTS_DIR / "report.txt"