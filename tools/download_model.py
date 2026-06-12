"""
Загрузка LLM для пайплайна ГородОК.

Запуск из корня проекта:
  .venv\\Scripts\\python.exe tools\\download_model.py

Модель кэшируется Hugging Face (~8 ГБ). Нужна для режимов с LLM.
"""

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
)

print(f"Загрузка модели {MODEL_NAME} (4-bit). Это может занять несколько минут...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True,
)

print("Модель загружена. Можно запускать LLM-режимы пайплайна.")
