import argparse
from pathlib import Path

import pandas as pd
import re

from cleaning_stats import save_cleaning_stats
from columns import CLEANED_COLUMNS, select_columns

# ==========================================
# Настройки
# ==========================================

DEFAULT_INPUT = "storage/samples/тестовый файл.xlsx"
DEFAULT_OUTPUT = "cleaned.xlsx"


def parse_args():
    parser = argparse.ArgumentParser(description="Очистка и фильтрация обращений")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()

# ==========================================
# Очистка текста
# ==========================================

def clean_text(text):
    if pd.isna(text):
        return ""

    text = str(text)

    # нижний регистр
    text = text.lower()

    # ссылки
    text = re.sub(r"http\S+", " ", text)

    # html теги
    text = re.sub(r"<[^>]+>", " ", text)

    # vk-разметка
    # [club123|текст]
    text = re.sub(r"\[[^\]|]+\|([^\]]+)\]", r"\1", text)

    # упоминания @user
    text = re.sub(r"@\w+", " ", text)

    # эмодзи и прочие символы
    text = re.sub(
        r"[^\w\s.,!?;:()%\-№/]",
        " ",
        text,
        flags=re.UNICODE
    )

    # популярные рекламные хвосты
    garbage_phrases = [
        "из омска? подпишись",
        "подпишись",
        "подписывайтесь",
        "источник:",
    ]

    for phrase in garbage_phrases:
        text = text.replace(phrase, " ")

    # переносы строк
    text = text.replace("\n", " ")

    # табуляции
    text = text.replace("\t", " ")

    # множественные пробелы
    text = re.sub(r"\s+", " ", text)

    return text.strip()

TEXT_COLUMN = "Текст инцидента"
TYPE_COLUMN = "Тип инцидента"
OUTCOME_COLUMN = "Итог"
CREATED_DATE_COLUMN = "Дата создания"

VALID_TYPES = ["Решаемый"]
OPEN_OUTCOMES = {"Не решено", "Отложено"}


def is_open_outcome(value):
    if pd.isna(value):
        return True
    text = str(value).strip()
    return text == "" or text in OPEN_OUTCOMES


def preprocess(input_file, output_file):
    print(f"Загрузка {input_file}...")
    df = pd.read_excel(input_file)
    start_count = len(df)
    print(f"Загружено строк: {start_count}")

    if TEXT_COLUMN not in df.columns:
        raise KeyError(f"Колонка '{TEXT_COLUMN}' не найдена: {list(df.columns)}")
    if TYPE_COLUMN not in df.columns:
        raise KeyError(f"Колонка '{TYPE_COLUMN}' не найдена: {list(df.columns)}")
    if OUTCOME_COLUMN not in df.columns:
        raise KeyError(f"Колонка '{OUTCOME_COLUMN}' не найдена: {list(df.columns)}")

    types_in_file = (
        df[TYPE_COLUMN].fillna("не указан").astype(str).value_counts().to_dict()
    )
    outcomes_in_file = (
        df[OUTCOME_COLUMN].fillna("не указан").astype(str).value_counts().to_dict()
    )

    print("Очистка текста...")
    df["Очищенный текст"] = df[TEXT_COLUMN].apply(clean_text)

    before = len(df)
    df = df[df["Очищенный текст"] != ""]
    removed_empty = before - len(df)
    print(f"Удалено пустых: {removed_empty}")

    before = len(df)
    df = df[df[TYPE_COLUMN].isin(VALID_TYPES)]
    removed_by_type = before - len(df)
    print(f"Удалено по типу (оставлен только «Решаемый»): {removed_by_type}")
    print(df[TYPE_COLUMN].value_counts())

    before = len(df)
    df = df[df[OUTCOME_COLUMN].apply(is_open_outcome)]
    removed_by_outcome = before - len(df)
    print(f"Удалено по итогу (закрытые обращения): {removed_by_outcome}")
    print(df[OUTCOME_COLUMN].value_counts(dropna=False))

    before = len(df)
    df = df.drop_duplicates(subset=["Очищенный текст"])
    removed_duplicates = before - len(df)
    print(f"Удалено дублей: {removed_duplicates}")

    df = select_columns(df, CLEANED_COLUMNS)

    stats = {
        "total_input": start_count,
        "total_after_clean": len(df),
        "removed_empty": removed_empty,
        "removed_by_type": removed_by_type,
        "removed_by_outcome": removed_by_outcome,
        "removed_duplicates": removed_duplicates,
        "types_in_file": types_in_file,
        "outcomes_in_file": outcomes_in_file,
    }
    stats_path = Path(output_file).with_name("cleaning_stats.json")
    save_cleaning_stats(stats, stats_path)
    print(f"Статистика очистки: {stats_path}")

    df.to_excel(output_file, index=False)
    print(f"Сохранено: {output_file} ({len(df)} строк из {start_count})")
    return df


def main():
    args = parse_args()
    preprocess(args.input, args.output)


if __name__ == "__main__":
    main()