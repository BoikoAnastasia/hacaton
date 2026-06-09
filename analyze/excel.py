import argparse
import pandas as pd
import re

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

    print("Очистка текста...")
    df["Очищенный текст"] = df[TEXT_COLUMN].apply(clean_text)

    before = len(df)
    df = df[df["Очищенный текст"] != ""]
    print(f"Удалено пустых: {before - len(df)}")

    before = len(df)
    df = df[df[TYPE_COLUMN].isin(VALID_TYPES)]
    print(f"Удалено по типу (оставлен только «Решаемый»): {before - len(df)}")
    print(df[TYPE_COLUMN].value_counts())

    before = len(df)
    df = df[df[OUTCOME_COLUMN].apply(is_open_outcome)]
    print(f"Удалено по итогу (закрытые обращения): {before - len(df)}")
    print(df[OUTCOME_COLUMN].value_counts(dropna=False))

    before = len(df)
    df = df.drop_duplicates(subset=["Очищенный текст"])
    print(f"Удалено дублей: {before - len(df)}")

    df = select_columns(df, CLEANED_COLUMNS)

    df.to_excel(output_file, index=False)
    print(f"Сохранено: {output_file} ({len(df)} строк из {start_count})")
    return df


def main():
    args = parse_args()
    preprocess(args.input, args.output)


if __name__ == "__main__":
    main()