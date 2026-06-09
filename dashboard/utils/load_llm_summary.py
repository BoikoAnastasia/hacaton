from core.config import DATA_FILE_SUMMARY

def load_llm_summary():
  if DATA_FILE_SUMMARY.exists():
    return DATA_FILE_SUMMARY.read_text(encoding="utf-8")
  return "Выводы пока не сформированы."