"""Определение: есть ли в обращении реальная проблема (а не благодарность)."""

import re

NOT_PROBLEM_RE = re.compile(
    r"(спасибо|благодар|поздравл|информир|уведомлен|"
    r"получил смс|прислали смс|репост|подписывайтесь|"
    r"хорошая работа|молодцы|отлично|молодц)",
    re.IGNORECASE,
)

# Похвала, благодарность, констатация что всё хорошо
POSITIVE_FEEDBACK_RE = re.compile(
    r"(?:"
    r"после\s+(?:расчистк|уборк|очистк|чистк)|"
    r"(?:расчистил|убрал|почистил|очистил)\w*|"
    r"буд(?:ет|ит)\s+до\s+следующ\w+\s+снегопад|"
    r"до\s+следующ\w+\s+снегопад|"
    r"держ(?:ится|атся)\s+до\s+следующ|"
    r"чист\w+\s+дорог|"
    r"дорог\w*\s+чист|"
    r"хорош\w+\s+работ|"
    r"отличн\w+\s+работ|"
    r"молодц|"
    r"благодар|"
    r"спасибо|"
    r"молодцы|"
    r"отлично|"
    r"👍|👏|❤|💪"
    r")",
    re.IGNORECASE,
)

# Явные жалобы и негатив
COMPLAINT_RE = re.compile(
    r"(?:"
    r"не\s+(?:убира|чист|вывоз|расчищ|работ)|"
    r"не\s+убран|"
    r"жалоб|"
    r"когда\s+уже|"
    r"до\s+сих\s+пор|"
    r"сколько\s+можно|"
    r"безобраз|"
    r"ужас|"
    r"кошмар|"
    r"разберитесь|"
    r"требуем|"
    r"возмут|"
    r"просим\s+убрать|"
    r"просим\s+принять\s+мер|"
    r"нет\s+(?:вод|свет|отоплен|газ)|"
    r"без\s+(?:вод|свет|отоплен|газ)"
    r")",
    re.IGNORECASE,
)

PROBLEM_RE = re.compile(
    r"(?:"
    r"проблем|"
    r"не\s+работ|"
    r"не\s+убира|"
    r"не\s+вывоз|"
    r"не\s+чист|"
    r"авар|"
    r"прорва|"
    r"слом|"
    r"отключ|"
    r"опасн|"
    r"угроз|"
    r"жалоб|"
    r"разбит|"
    r"яма|"
    r"затоп|"
    r"грязн|"
    r"не\s+горит|"
    r"не\s+свет|"
    r"мусор|"
    r"гололед|"
    r"отсутств|"
    r"занес|"
    r"неисправ|"
    r"без\s+вод|"
    r"без\s+свет|"
    r"без\s+отоп|"
    r"снег(?!опад)|"
    r"лед(?!и)"
    r")",
    re.IGNORECASE,
)


def is_positive_feedback(text: str) -> bool:
    if not text or not str(text).strip():
        return False
    text = str(text)
    if not POSITIVE_FEEDBACK_RE.search(text):
        return False
    # Похвала без жалобы — не проблема
    return not COMPLAINT_RE.search(text)


def has_complaint_signal(text: str) -> bool:
    if not text:
        return False
    text = str(text)
    return bool(COMPLAINT_RE.search(text) or (
        PROBLEM_RE.search(text) and not is_positive_feedback(text)
    ))


def refine_problem(
    llm_problem: bool | None,
    text: str,
    theme: str | None = None,
    group: str | None = None,
) -> bool:
    """LLM + правила: отсекаем ложные проблемы (благодарности, похвалу)."""
    text = str(text or "")

    if is_positive_feedback(text):
        return False

    if has_complaint_signal(text):
        return True

    if NOT_PROBLEM_RE.search(text) and not PROBLEM_RE.search(text):
        return False

    if llm_problem is not None:
        # Тема про уборку/дороги без жалобы в тексте — не проблема
        if bool(llm_problem) and not has_complaint_signal(text):
            theme_group = f"{theme or ''} {group or ''}".lower()
            if re.search(r"уборк|дорог|снег|налед|благоустройств", theme_group):
                return False
        return bool(llm_problem)

    return has_complaint_signal(text)
