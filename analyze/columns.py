"""Порядок и названия колонок в cleaned.xlsx и result.xlsx."""

SOURCE_COLUMNS = [
    "Дата создания",
    "Муниципалитет",
    "Населенный пункт",
    "Улица",
    "Дом",
    "Группа тем",
    "Тема",
    "Тип инцидента",
    "Текст инцидента",
    "Итог",
]

DERIVED_COLUMNS = [
    "Очищенный текст",
]

COL_PROBLEM = "Проблема"
COL_SEVERITY = "Серьёзность"
COL_SEVERITY_LABEL = "Уровень серьёзности"
COL_SUMMARY = "Суть проблемы"

ANALYSIS_COLUMNS = [
    COL_PROBLEM,
    COL_SEVERITY,
    COL_SEVERITY_LABEL,
    COL_SUMMARY,
]

LEGACY_ANALYSIS_MAP = {
    "problem": COL_PROBLEM,
    "severity": COL_SEVERITY,
    "summary": COL_SUMMARY,
}

CLEANED_COLUMNS = SOURCE_COLUMNS + DERIVED_COLUMNS
RESULT_COLUMNS = CLEANED_COLUMNS + ANALYSIS_COLUMNS


def normalize_analysis_columns(df):
    """Поддержка старых result.xlsx с английскими именами колонок."""
    rename = {
        old: new
        for old, new in LEGACY_ANALYSIS_MAP.items()
        if old in df.columns and new not in df.columns
    }
    if rename:
        df = df.rename(columns=rename)
    return df


def select_columns(df, columns):
    return df[[col for col in columns if col in df.columns]]


def attach_severity_labels(df):
    import pandas as pd

    from severity_utils import severity_label

    if COL_SEVERITY in df.columns:
        df[COL_SEVERITY_LABEL] = df[COL_SEVERITY].apply(
            lambda v: severity_label(int(v)) if pd.notna(v) else ""
        )
    return df
