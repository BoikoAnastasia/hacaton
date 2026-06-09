"""Правила и пост-обработка колонки «Серьёзность» (LLM + ключевые слова + тема).

Шкала 0–5. Уровень 5 — только критические ситуации, которые не терпят отлагательств
(угроза жизни/здоровью, отсутствие жизненно важных услуг, авария, прорыв, пожар).
"""

import re

from problem_utils import COMPLAINT_RE, has_complaint_signal, is_positive_feedback

# Уровень 5 разрешён только при явных маркерах срочной критичности в тексте
CRITICAL_URGENT_RE = re.compile(
    r"(?:"
    r"нет\s+(?:вод|газ|отоплен|электр|свет)|"
    r"отсутств(?:ует|ует).*?(?:вод|газ|отоплен|электр|свет)|"
    r"без\s+(?:вод|газ|отоплен|электр|свет)|"
    r"\d+\s*(?:день|дня|дней|суток)\s+без\s+(?:вод|газ|отоплен|электр|свет)|"
    r"прорвало|прорвал|авария|обрушен|затоплен|"
    r"утечк.*газ|угроза\s+жизн|угроза\s+здоров|"
    r"скорая\s+не\s+(?:может|доех)|"
    r"мороз.*без\s+отоплен|"
    r"пожар|задымлен|"
    r"не\s+терпит\s+отлагательств|"
    r"срочн(?:о|ая)|"
    r"экстренн"
    r")",
    re.IGNORECASE,
)

TEXT_SEVERITY_RULES = [
    (5, CRITICAL_URGENT_RE),
    (4, re.compile(
        r"(весь\s+(?:микрорайон|район|подъезд|двор|дом)|"
        r"все\s+дом|несколько\s+дом|"
        r"пос[её]лок|деревн|"
        r"критич|многоквартирн|"
        r"не\s+(?:можем|могут)\s+(?:выйти|вызвать)|"
        r"уже\s+(?:неделю|2\s+недел)|"
        r"отключил(?:и|о)\s+(?:вод|газ|отоплен|электр|свет))",
        re.IGNORECASE,
    )),
    (3, re.compile(
        r"(не\s+работает|несколько\s+месяц|"
        r"уже\s+месяц|не\s+вывозят|не\s+убирают|"
        r"давно\s+не|постоянно|систематическ|"
        r"каждый\s+(?:год|раз|день)|"
        r"повторя(?:ется|ующ)|"
        r"опасн(?:о|ая|ый)|"
        r"не\s+(?:ремонтир|устран))",
        re.IGNORECASE,
    )),
    (2, re.compile(
        r"(снег(?!опад)|"
        r"мусор|яма|освещен|дорог|тротуар|"
        r"остановк|пешеход|гололед|лед(?!и)|"
        r"реагент|грейдер|коммунал|"
        r"грязн|не\s+чист|не\s+убран|"
        r"разбит|не\s+горит|не\s+свет)",
        re.IGNORECASE,
    )),
    (1, re.compile(
        r"(урн|скамейк|лампочк|фонар|мелк|"
        r"некрасив|граффити|"
        r"шум|запах|вывеск)",
        re.IGNORECASE,
    )),
]

THEME_SEVERITY_HINTS = [
    (4, re.compile(
        r"вод|газ|отоплен|электр|авар|прорв|затоп|"
        r"обрушен|пожар|газоснабжен|холодн(?:ая|ое)\s+вод",
        re.IGNORECASE,
    )),
    (3, re.compile(
        r"мусор|вывоз|канализац|"
        r"мед(?:ицин|помощ)|"
        r"скорая|"
        r"жил(?:ой|ые)\s+фонд|"
        r"управляющ|"
        r"многоквартирн",
        re.IGNORECASE,
    )),
    (2, re.compile(
        r"транспорт|автобус|дорог|"
        r"освещен|"
        r"благоустройств|"
        r"двор|"
        r"уборк|"
        r"снег|налед",
        re.IGNORECASE,
    )),
]

GROUP_SEVERITY_HINTS = [
    (3, re.compile(r"жкх|коммунал|водоканал|энерг|газ", re.IGNORECASE)),
    (2, re.compile(r"дорог|транспорт|благоустройств|двор", re.IGNORECASE)),
]

SEVERITY_LABELS = {
    0: "нет проблемы",
    1: "низкая",
    2: "умеренная",
    3: "значимая",
    4: "серьёзная",
    5: "критическая, не терпит отлагательств",
}


def is_critical_urgent(text: str) -> bool:
    """Уровень 5 допустим только при признаках срочной критичности в тексте."""
    return bool(text and CRITICAL_URGENT_RE.search(str(text)))


def _apply_hints(label: str | None, hints: list[tuple[int, re.Pattern]], level: int) -> int:
    if not label:
        return level
    text = str(label)
    for sev, pattern in hints:
        if pattern.search(text):
            level = max(level, sev)
    return level


def severity_from_text(text: str) -> int:
    if not text:
        return 0
    level = 0
    for sev, pattern in TEXT_SEVERITY_RULES:
        if pattern.search(text):
            level = max(level, sev)
    return level


def severity_from_hints(theme: str | None = None, group: str | None = None) -> int:
    level = 0
    level = _apply_hints(theme, THEME_SEVERITY_HINTS, level)
    level = _apply_hints(group, GROUP_SEVERITY_HINTS, level)
    return level


def rule_severity(
    text: str,
    theme: str | None = None,
    group: str | None = None,
) -> int:
    text_level = severity_from_text(text)
    hint_level = severity_from_hints(theme, group)

    if is_positive_feedback(text):
        return 0

    if COMPLAINT_RE.search(text):
        return max(text_level, hint_level)

    if text_level > 0:
        return max(text_level, min(hint_level, text_level + 1))

    # Только тема/группа без жалобы в тексте — не выше 2
    return min(hint_level, 2)


def severity_label(level: int) -> str:
    return SEVERITY_LABELS.get(int(level), "умеренная")


def refine_severity(
    llm_severity: int | None,
    text: str,
    theme: str | None = None,
    group: str | None = None,
    is_problem: bool = True,
) -> int:
    if not is_problem:
        return 0

    if is_positive_feedback(text):
        return 0

    text_level = severity_from_text(text)
    rule = rule_severity(text, theme, group)
    llm = 0 if llm_severity is None else int(llm_severity)

    # LLM не может «придумать» критичность без сильных маркеров в тексте
    if text_level < 4:
        if not has_complaint_signal(text):
            llm = min(llm, 2)
        else:
            llm = min(llm, text_level + 1)

    if rule >= 4:
        merged = min(5, max(llm, rule))
    elif llm <= 0 and rule <= 0:
        merged = 2 if has_complaint_signal(text) else 1
    else:
        merged = min(5, max(llm, rule))

    # 5 — только при критической срочности; иначе потолок 4
    if merged == 5 and not is_critical_urgent(text):
        merged = 4

    return merged
