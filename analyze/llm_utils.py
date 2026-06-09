import json
import os
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

json_regex = re.compile(r"\{[^{}]*\}", re.DOTALL)
ru_regex = re.compile(r"[а-яА-ЯёЁ]")
bad_regex = re.compile(r"[a-zA-Z]|[^\u0000-\u007F\u0400-\u04FF\s\d.,!?()-]")


def build_prompt(text, theme=None, group=None, compact=False):
    context = ""
    if group and str(group).strip():
        context += f"Группа тем: {group}\n"
    if theme and str(theme).strip():
        context += f"Тема: {theme}\n"

    if compact:
        return f"""Аналитик обращений. Определи problem и severity.
Верни ТОЛЬКО JSON: {{"problem": true/false, "severity": 0-5}}

Группа тем и Тема — предварительная классификация оператора.
Если текст явно противоречит теме — доверяй тексту.

Шкала severity:
0 — нет проблемы (благодарность, информация)
1 — мелочь (урна, лампочка)
2 — локально (снег, яма, мусор, освещение)
3 — затянулось (неделя+, постоянно, не убирают)
4 — серьёзно (массово, весь дом/район, длительное отключение услуги)
5 — КРИТИЧЕСКАЯ, НЕ ТЕРПИТ ОТЛАГАТЕЛЬСТВ: угроза жизни/здоровью, нет воды/газа/отопления/света, авария, прорыв, пожар, утечка газа. Ставь 5 ТОЛЬКО в таких случаях. Снег, мусор, ямы — максимум 3–4.

Примеры:
{{"problem": true, "severity": 2}} — не убран снег у подъезда
{{"problem": true, "severity": 5}} — 3 дня без воды, маленький ребёнок
{{"problem": false, "severity": 0}} — спасибо за работу

Жалоба в тексте → problem=true, даже если в конце «спасибо».

{context}Текст:
{text}"""

    return f"""Ты аналитик обращений граждан.

Твоя задача определить:
1. Есть ли реальная проблема (жалоба, неисправность, угроза, неудобство для жителей).
2. Краткую суть проблемы своими словами (НЕ копируй текст обращения).
3. Степень тяжести.

Шкала тяжести:
0 - проблемы нет (только благодарность, поздравление, информация)
1 - мелкое неудобство
2 - локальная проблема
3 - значимая проблема
4 - серьёзная проблема для группы жителей
5 - КРИТИЧЕСКАЯ, НЕ ТЕРПИТ ОТЛАГАТЕЛЬСТВ: угроза жизни/здоровью, отсутствие воды/газа/отопления/света, авария, прорыв, пожар. Ставь 5 ТОЛЬКО когда нужны немедленные действия. Бытовые жалобы (снег, мусор, ямы) — не выше 4.

ВАЖНО:
- Группа тем и Тема — подсказка оператора; при конфликте с текстом доверяй тексту.
- Если в тексте есть жалоба, это problem=true, даже если в конце написано "спасибо".
- summary — перефразируй суть в 5-10 словах на русском, можно опереться на тему, добавь детали из текста (срок, масштаб).
- Несколько дней без воды/отопления при угрозе здоровью — severity 5; иначе 4.

{context}
Примеры:

Текст: На остановке отсутствует урна.
Ответ: {{"problem": true, "severity": 1, "summary": "отсутствует урна на остановке"}}

Текст: 2 дня без воды, порыв трубы, маленький ребёнок. Заранее спасибо.
Ответ: {{"problem": true, "severity": 5, "summary": "два дня без воды после порыва трубы"}}

Текст: Спасибо администрации за благоустройство парка.
Ответ: {{"problem": false, "severity": 0, "summary": "благодарность за благоустройство"}}

Верни только валидный JSON. Без markdown.

Текст обращения:
{text}"""


def load_model():
    print("Загрузка модели...")

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
        local_files_only=True,
        low_cpu_mem_usage=True,
    )
    model.eval()
    print("Модель загружена")
    return tokenizer, model


def extract_json(text):
    cleaned = text.replace("```json", "").replace("```", "").strip()
    match = json_regex.search(cleaned)
    if not match:
        raise ValueError("JSON not found")
    return json.loads(match.group(0))


def is_valid_russian(text):
    if not text:
        return False
    return len(ru_regex.findall(text)) >= 3 and bad_regex.search(text) is None


def normalize_result(raw, compact=False):
    result = extract_json(raw)
    problem = bool(result.get("problem", False))
    severity = int(result.get("severity", 0))
    summary = str(result.get("summary", "")).strip() if not compact else ""

    if problem and severity == 0:
        severity = 1
    if not problem:
        severity = 0

    if not compact and not is_valid_russian(summary):
        summary = "ошибка генерации"

    return problem, severity, summary


@torch.inference_mode()
def generate_batch(texts, themes, groups, tokenizer, model, compact=False):
    messages = [
        [{"role": "user", "content": build_prompt(t, th, gr, compact=compact)}]
        for t, th, gr in zip(texts, themes, groups)
    ]
    chat_texts = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        chat_texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=1536 if compact else 2048,
    ).to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=40 if compact else 100,
        do_sample=False,
        pad_token_id=tokenizer.pad_token_id,
        use_cache=True,
    )

    input_len = inputs["input_ids"].shape[1]
    return [
        tokenizer.decode(outputs[i][input_len:], skip_special_tokens=True).strip()
        for i in range(len(texts))
    ]


def analyze_batch(texts, themes, groups, tokenizer, model, compact=False):
    themes = themes or [None] * len(texts)
    groups = groups or [None] * len(texts)

    try:
        responses = generate_batch(texts, themes, groups, tokenizer, model, compact=compact)
    except Exception:
        responses = [""] * len(texts)

    results = []
    for text, theme, group, response in zip(texts, themes, groups, responses):
        try:
            results.append(normalize_result(response, compact=compact))
        except Exception:
            try:
                single = generate_batch([text], [theme], [group], tokenizer, model, compact=compact)[0]
                results.append(normalize_result(single, compact=compact))
            except Exception:
                results.append((None, None, "ошибка парсинга"))
    return results
