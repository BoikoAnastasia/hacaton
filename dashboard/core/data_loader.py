import pandas as pd
from core.config import DATA_FILE_RESULT, DATA_FILE_TOP_10

def load_main_df():
  if DATA_FILE_RESULT.exists():
    return pd.read_excel(DATA_FILE_RESULT)
  return None


def load_top10_df():
  if DATA_FILE_TOP_10.exists():
    return pd.read_excel(DATA_FILE_TOP_10)
  return None