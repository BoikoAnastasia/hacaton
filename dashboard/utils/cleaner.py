import pandas as pd

def clean(val):
  if pd.isna(val):
    return ""
  return str(val).strip()