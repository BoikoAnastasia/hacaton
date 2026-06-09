"""Краткие описания проблем для колонки «Суть проблемы» (без LLM)."""

import re

import pandas as pd

from problem_utils import NOT_PROBLEM_RE, is_positive_feedback

PROBLEM_RE = re.compile(
    r"(проблем|не работ|нет |не убира|не вывоз|не чист|"
    r"авар|прорва|слом|отключ|опасн|угроз|жалоб|"
    r"разбит|яма|затоп|грязн|не горит|не свет|"
    r"мусор|снег|лед|гололед|отсутств|занес|неисправ|"
    r"прорв|затоп|копт|без\s+вод|без\s+свет|без\s+отоп)",
    re.IGNORECASE,
)

NOISE_PREFIX_RE = re.compile(
    r"^(?:уважаем\w*|здравств\w*|добр\w+(?:\s+\w+)?|"
    r"прошу(?:\s+вас)?|скажите\s+пожалуйста|подскажите|"
    r"обраща\w*|да\s+когда|нет\s+слов|хочется\s+получить\s+ответ|"
    r"интересно\s+когда)[\s,!.?—-]*",
    re.IGNORECASE,
)

FILLER_SENT_RE = re.compile(
    r"^(?:уважаем|здравств|прошу|скажите|подскаж|обраща|"
    r"администрац|роспотреб|водоканал|г\.?\s*омск|"
    r"магнит|гибдд|департамент)[\s!,.]",
    re.IGNORECASE,
)

ADDRESS_RE = re.compile(
    r"(?:"
    r"ул\.?\s+[\w«»\"'\d\s.-]{2,30}|"
    r"улиц\w+\s+[\w«»\"'\d\s.-]{2,30}|"
    r"пр\.?\s+[\w«»\"'\d\s.-]{2,30}|"
    r"пер\.?\s+[\w«»\"'\d\s.-]{2,30}|"
    r"мкр\.?\s+[\w\d.-]{2,20}|"
    r"микрорайон\s+[\w\d\s.-]{2,25}|"
    r"д\.?\s*\d{1,4}|"
    r"дом\s+\d{1,4}"
    r")",
    re.IGNORECASE,
)

DETAIL_PATTERNS = [
    re.compile(r"\d+\s*(?:день|дня|дней|суток)\s+(?:без|уже|нет)", re.IGNORECASE),
    re.compile(r"(?:уже\s+)?\d+\s*(?:недел\w*|месяц\w*)", re.IGNORECASE),
    re.compile(r"весь\s+(?:дом|подъезд|двор|район|микрорайон|пос[её]лок)", re.IGNORECASE),
    re.compile(r"несколько\s+(?:дом|подъезд|двор)", re.IGNORECASE),
    re.compile(r"постоянно|систематическ|каждый\s+(?:день|раз)", re.IGNORECASE),
]

MAX_WORDS = 10
ERROR_SUMMARIES = frozenset({"ошибка парсинга", "ошибка генерации"})


def _clean_field(value) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def _strip_noise(text: str) -> str:
    cleaned = text.strip()
    while cleaned:
        nxt = NOISE_PREFIX_RE.sub("", cleaned).strip()
        if nxt == cleaned:
            break
        cleaned = nxt
    return cleaned


def _sentences(text: str) -> list[str]:
    parts = re.split(r"[.!?;\n]+", text)
    return [p.strip() for p in parts if len(p.strip()) >= 12]


def _pick_problem_sentence(text: str) -> str:
    scored: list[tuple[int, str]] = []
    for sent in _sentences(text):
        if FILLER_SENT_RE.search(sent):
            score = 0
        elif PROBLEM_RE.search(sent):
            score = 5 + len(PROBLEM_RE.findall(sent))
        else:
            score = 1
        scored.append((score, sent))

    if not scored:
        return _strip_noise(text)

    scored.sort(key=lambda x: (-x[0], -len(x[1])))
    best_score, best = scored[0]
    if best_score > 0:
        return _strip_noise(best)
    return _strip_noise(text)


def _shorten_label(label: str | None) -> str | None:
    if not label or not str(label).strip():
        return None
    short = re.split(r"[(\[]", str(label).strip())[0].strip().lower()
    words = short.split()
    if len(words) <= MAX_WORDS:
        return short
    return " ".join(words[:MAX_WORDS])


def _extract_address(text: str) -> str | None:
    match = ADDRESS_RE.search(text)
    if not match:
        return None
    addr = re.sub(r"\s+", " ", match.group().strip().lower())
    if len(addr.split()) > 6 or any(w in addr for w in ("нет", "проблем", "администрац")):
        return None
    return addr[:40]


def _format_location(
    street: str | None = None,
    house: str | None = None,
    locality: str | None = None,
) -> str | None:
    parts: list[str] = []
    locality_s = _clean_field(locality)
    street_s = _clean_field(street)
    house_s = _clean_field(house)

    if locality_s:
        parts.append(locality_s.lower())
    if street_s:
        street_fmt = street_s.lower()
        if not re.match(r"^(ул\.?|улиц)", street_fmt):
            street_fmt = f"ул. {street_fmt}"
        parts.append(street_fmt[:30])
    if house_s:
        house_fmt = house_s.lower()
        if not re.match(r"^д\.?", house_fmt):
            house_fmt = f"д. {house_fmt}"
        parts.append(house_fmt[:12])
    if not parts:
        return None
    return ", ".join(parts)[:55]


def _extract_detail(text: str) -> str | None:
    details: list[str] = []
    for pattern in DETAIL_PATTERNS:
        match = pattern.search(text)
        if match:
            detail = re.sub(r"\s+", " ", match.group().strip().lower())
            if detail not in details:
                details.append(detail)
        if len(details) >= 2:
            break
    return ", ".join(details) if details else None


def _words_from_problem(sentence: str) -> str:
    words = sentence.split()
    if not words:
        return sentence

    start = 0
    for i, word in enumerate(words):
        if PROBLEM_RE.search(word):
            start = max(0, i - 1)
            break
        if i >= 4:
            start = i - 3
            break

    chunk = words[start : start + MAX_WORDS]
    return " ".join(chunk)


def _capitalize_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _join_summary_parts(parts: list[str]) -> str:
    seen: list[str] = []
    combined = ""
    for part in parts:
        part = part.strip(" ,.;")
        if not part:
            continue
        low = part.lower()
        if low in combined.lower():
            continue
        seen.append(part)
        combined = f"{combined}, {part}" if combined else part
    return _capitalize_first(combined.strip(" ,.;")[:120])


def merge_llm_summary(rule_summary: str, llm_summary: str | None) -> str:
    """Берём rule-based суть и при необходимости обогащаем ответом LLM."""
    if not llm_summary or llm_summary in ERROR_SUMMARIES:
        return rule_summary
    llm = llm_summary.strip().lower()
    if len(llm) < 8:
        return rule_summary
    if rule_summary.lower() in llm or llm in rule_summary.lower():
        return rule_summary if len(rule_summary) >= len(llm) else _capitalize_first(llm)
    return _join_summary_parts([rule_summary, llm])


def make_summary(
    text: str,
    is_problem: bool,
    theme: str | None = None,
    group: str | None = None,
    street: str | None = None,
    house: str | None = None,
    locality: str | None = None,
) -> str:
    if not text or not str(text).strip():
        return "Пустое обращение"

    if not is_problem:
        if is_positive_feedback(text) or NOT_PROBLEM_RE.search(text):
            return "Благодарность или положительный отзыв"
        return "Обращение без проблемы"

    theme_short = _shorten_label(theme)
    group_short = _shorten_label(group) if not theme_short else None
    detail = _extract_detail(str(text))
    location = _format_location(street, house, locality) or _extract_address(str(text))

    if theme_short:
        base = theme_short
    elif group_short:
        base = group_short
    else:
        problem_sent = _pick_problem_sentence(str(text))
        base = _words_from_problem(problem_sent) or "проблема в обращении"

    parts = [base]
    if detail and detail.lower() not in base.lower():
        parts.append(detail)
    if location and location.lower() not in " ".join(parts).lower():
        parts.append(location)

    result = _join_summary_parts(parts)
    return result if result else "Проблема в обращении"


def make_summary_from_row(row, text: str, is_problem: bool) -> str:
    return make_summary(
        text=text,
        is_problem=is_problem,
        theme=row.get("Тема"),
        group=row.get("Группа тем"),
        street=row.get("Улица"),
        house=row.get("Дом"),
        locality=row.get("Населенный пункт"),
    )
