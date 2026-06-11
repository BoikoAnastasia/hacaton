"""
LLM-саммари только для Top-N районов (~2-5 минут).
Используется после fast_analyze + aggregate.
"""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import argparse
import json
import re
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from columns import COL_PROBLEM, normalize_analysis_columns
from location_utils import make_district_key
from pdf_report import generate_pdf_from_report_xlsx

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
json_regex = re.compile(r"\{[^{}]*\}", re.DOTALL)


def parse_args():
    parser = argparse.ArgumentParser(description="LLM-описание топ районов")
    parser.add_argument("--input", required=True, help="result.xlsx после анализа")
    parser.add_argument("--report", required=True, help="report.xlsx с листом Топ-10")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--output", default=None, help="Обновлённый report.xlsx")
    return parser.parse_args()


def load_model():
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quant,
        device_map="auto",
        trust_remote_code=True,
        local_files_only=True,
    )
    model.eval()
    return tokenizer, model


@torch.inference_mode()
def generate(text, tokenizer, model):
    prompt = f"""Ты аналитик. На основе обращений граждан опиши ключевые проблемы района.
Верни ТОЛЬКО JSON: {{"причины": "краткое описание до 30 слов на русском"}}

Обращения:
{text}"""

    messages = [[{"role": "user", "content": prompt}]]
    chat = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(chat, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=80,
        do_sample=False,
        pad_token_id=tokenizer.pad_token_id,
    )
    gen = outputs[0][inputs["input_ids"].shape[1]:]
    raw = tokenizer.decode(gen, skip_special_tokens=True).strip()

    match = json_regex.search(raw.replace("```json", "").replace("```", ""))
    if match:
        return json.loads(match.group(0)).get("причины", raw[:100])
    return raw[:100]


def get_district_examples(df, district, n=8):
    keys = df.apply(make_district_key, axis=1)
    mask = keys == district
    problems = df[mask & (df[COL_PROBLEM] == True)]  # noqa: E712
    col = next((c for c in ("Очищенный текст", "clean_text", "Текст инцидента") if c in problems.columns), None)
    if col is None:
        return ""
    return "\n".join(problems[col].dropna().head(n).astype(str).tolist())


def main():
    args = parse_args()
    df = normalize_analysis_columns(pd.read_excel(args.input))
    top_df = pd.read_excel(args.report, sheet_name="Топ-10")

    print("Загрузка LLM...")
    tokenizer, model = load_model()

    descriptions = []
    for _, row in top_df.head(args.top).iterrows():
        district = row["район"]
        examples = get_district_examples(df, district)
        print(f"Район: {district}")
        desc = generate(examples[:2000], tokenizer, model) if examples else row.get("ключевые_проблемы", "")
        descriptions.append(desc)
        print(f"  -> {desc}")

    top_df = top_df.copy()
    top_df.loc[: len(descriptions) - 1, "описание_llm"] = descriptions

    output = args.output or args.report
    top3 = pd.read_excel(args.report, sheet_name="Топ-3")
    all_districts = pd.read_excel(args.report, sheet_name="Все районы")
    overview = pd.read_excel(args.report, sheet_name="Обзор")

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        top_df.to_excel(writer, sheet_name="Топ-10", index=False)
        top3.to_excel(writer, sheet_name="Топ-3", index=False)
        all_districts.to_excel(writer, sheet_name="Все районы", index=False)
        overview.to_excel(writer, sheet_name="Обзор", index=False)

    from export_names import KIND_SUMMARY, export_path

    pdf_path = export_path(Path(output).parent, KIND_SUMMARY)
    generate_pdf_from_report_xlsx(output, pdf_path)
    print(f"Обновлён: {output}")
    print(f"PDF-справка: {pdf_path}")


if __name__ == "__main__":
    main()
