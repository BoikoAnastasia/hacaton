# download_model.py
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch

# Настройка 4-битного квантования для экономии памяти [citation:4][citation:10]
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

# Укажите имя модели на Hugging Face
model_name = "Qwen/Qwen2.5-7B-Instruct"

print(f"Начинаю загрузку модели {model_name}. Это может занять время...")

# Загрузка токенизатора и модели
# Здесь и произойдет скачивание
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map="auto", # Автоматически распределяет на GPU, если она есть
    trust_remote_code=True # Нужно для некоторых моделей Qwen
)

print("Модель успешно загружена!")