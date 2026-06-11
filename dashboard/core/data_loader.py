import pandas as pd

from core.report_files import KIND_REPORT, KIND_RESULT, find_report_file


def load_main_df():
    path = find_report_file(KIND_RESULT)
    if path:
        return pd.read_excel(path)
    return None


def load_top10_df():
    path = find_report_file(KIND_REPORT)
    if path:
        return pd.read_excel(path)
    return None
