"""Генерация PDF-справки для руководства."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FONT_REGULAR = "ReportRegular"
FONT_BOLD = "ReportBold"

# Палитра в духе дашборда
COLOR_PRIMARY = colors.HexColor("#5B3ECA")
COLOR_HEADER_BG = colors.HexColor("#111827")
COLOR_CARD_BG = colors.HexColor("#1F2937")
COLOR_TEXT = colors.HexColor("#F9FAFB")
COLOR_MUTED = colors.HexColor("#9CA3AF")
COLOR_HIGH = colors.HexColor("#EF4444")
COLOR_MEDIUM = colors.HexColor("#F59E0B")
COLOR_LOW = colors.HexColor("#22C55E")
COLOR_ROW_ALT = colors.HexColor("#F3F4F6")
COLOR_BORDER = colors.HexColor("#E5E7EB")


def _font_candidates() -> list[tuple[str, str | None]]:
    windir = Path("C:/Windows/Fonts")
    return [
        (str(windir / "arial.ttf"), str(windir / "arialbd.ttf")),
        (str(windir / "calibri.ttf"), str(windir / "calibrib.ttf")),
        (str(windir / "segoeui.ttf"), str(windir / "segoeuib.ttf")),
        (str(windir / "times.ttf"), str(windir / "timesbd.ttf")),
    ]


def register_fonts() -> None:
    if FONT_REGULAR in pdfmetrics.getRegisteredFontNames():
        return

    for regular, bold in _font_candidates():
        if regular and Path(regular).exists():
            pdfmetrics.registerFont(TTFont(FONT_REGULAR, regular))
            bold_path = bold if bold and Path(bold).exists() else regular
            pdfmetrics.registerFont(TTFont(FONT_BOLD, bold_path))
            return

    raise RuntimeError(
        "Не найден TTF-шрифт с кириллицей. Установите Arial или Calibri в системе."
    )


def _severity_color(value: float) -> colors.Color:
    if value >= 4:
        return COLOR_HIGH
    if value >= 2.5:
        return COLOR_MEDIUM
    return COLOR_LOW


def _color_hex(color: colors.Color) -> str:
    return f"#{color.hexval()[2:].upper()}"


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=22,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=11,
            textColor=COLOR_MUTED,
            spaceAfter=0,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=14,
            textColor=COLOR_HEADER_BG,
            spaceBefore=10,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            textColor=colors.HexColor("#111827"),
            leading=14,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=9,
            textColor=COLOR_MUTED,
            leading=12,
        ),
        "card_title": ParagraphStyle(
            "card_title",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=10,
            textColor=colors.white,
        ),
        "card_value": ParagraphStyle(
            "card_value",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=18,
            textColor=colors.white,
            leading=22,
        ),
        "card_hint": ParagraphStyle(
            "card_hint",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8,
            textColor=COLOR_MUTED,
            leading=10,
        ),
        "district_name": ParagraphStyle(
            "district_name",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=11,
            textColor=colors.HexColor("#111827"),
            leading=14,
        ),
        "district_meta": ParagraphStyle(
            "district_meta",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=9,
            textColor=COLOR_MUTED,
            leading=12,
        ),
        "cell": ParagraphStyle(
            "cell",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=9,
            textColor=colors.HexColor("#111827"),
            leading=12,
        ),
        "cell_bold": ParagraphStyle(
            "cell_bold",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=9,
            textColor=colors.HexColor("#111827"),
            leading=12,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8,
            textColor=COLOR_MUTED,
            alignment=TA_CENTER,
        ),
    }


def _header_block(styles: dict[str, ParagraphStyle], generated_at: datetime) -> list:
    header_data = [[
        Paragraph("ГородОК", styles["title"]),
        Paragraph(
            f"Справка по проблемным районам<br/>"
            f"<font color='#9CA3AF'>Сформировано: {generated_at.strftime('%d.%m.%Y %H:%M')}</font>",
            styles["subtitle"],
        ),
    ]]
    header_table = Table(header_data, colWidths=[8 * cm, 9.5 * cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("BOX", (0, 0), (-1, -1), 0, COLOR_HEADER_BG),
    ]))
    return [header_table, Spacer(1, 12)]


def _kpi_card_cell(
    styles: dict[str, ParagraphStyle],
    title: str,
    value: str,
    hint: str | None,
    width: float,
) -> Table:
    rows = [
        [Paragraph(title, styles["card_title"])],
        [Paragraph(value, styles["card_value"])],
    ]
    if hint:
        rows.append([Paragraph(hint, styles["card_hint"])])

    cell = Table(rows, colWidths=[width])
    cell.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return cell


def _kpi_cards(
    styles: dict[str, ParagraphStyle],
    total_rows: int,
    total_problems: int,
    districts_count: int,
    problem_share: float,
    total_input: int | None = None,
    avg_severity: float | None = None,
) -> Table:
    col_w = 4.3 * cm

    if total_input and total_input != total_rows:
        first_title = "Всего обращений"
        first_value = str(total_input)
        first_hint = f"Нерешённых к анализу: {total_rows}"
    else:
        first_title = "Всего обращений"
        first_value = str(total_rows)
        first_hint = None

    problem_hint = None
    if total_rows and total_problems != total_rows:
        problem_hint = f"{problem_share:.1f}% от отобранных"

    severity_value = f"{avg_severity:.2f}" if avg_severity is not None else "—"

    cards = [
        (first_title, first_value, first_hint),
        ("Выявлено проблем", str(total_problems), problem_hint),
        ("Районов с проблемами", str(districts_count), None),
        ("Средняя тяжесть", severity_value, None),
    ]
    row = [
        _kpi_card_cell(styles, title, value, hint, col_w)
        for title, value, hint in cards
    ]

    table = Table([row], colWidths=[col_w] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_HEADER_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ]))
    return table


def _top3_cards(styles: dict[str, ParagraphStyle], top3: pd.DataFrame) -> list:
    if top3.empty:
        return [Paragraph("Проблемных обращений не выявлено.", styles["body"])]

    elements = [Paragraph("ТОП-3 проблемных района", styles["section"]), Spacer(1, 4)]
    card_cells = []

    for _, row in top3.iterrows():
        rank = int(row.get("ранг", len(card_cells) + 1))
        district = str(row["район"])
        count = int(row["количество_проблем"])
        severity = float(row["средняя_тяжесть"])
        issues = str(row.get("ключевые_проблемы", ""))[:220]
        sev_color = _severity_color(severity)

        content = [
            Paragraph(f"#{rank}  {district}", styles["district_name"]),
            Spacer(1, 2),
            Paragraph(
                f"Проблем: <b>{count}</b> · Средняя тяжесть: "
                f"<font color='{_color_hex(sev_color)}'><b>{severity:.1f}</b></font> / 5",
                styles["district_meta"],
            ),
            Spacer(1, 4),
            Paragraph(f"<b>Основные причины:</b> {issues or '—'}", styles["body"]),
        ]
        card_cells.append(content)

    table_rows = []
    for i in range(0, len(card_cells), 2):
        left = card_cells[i]
        right = card_cells[i + 1] if i + 1 < len(card_cells) else ""
        table_rows.append([left, right])

    cards_table = Table(table_rows, colWidths=[8.6 * cm, 8.6 * cm])

    cards_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 3, COLOR_PRIMARY),
        ("LINEBEFORE", (1, 0), (1, -1), 3, COLOR_PRIMARY),
        ("LINEBEFORE", (0, 1), (0, 1), 3, COLOR_PRIMARY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
    ]))
    elements.extend([cards_table, Spacer(1, 12)])
    return elements


def _top10_table(styles: dict[str, ParagraphStyle], top10: pd.DataFrame) -> list:
    if top10.empty:
        return []

    header = [
        Paragraph("№", styles["cell_bold"]),
        Paragraph("Район", styles["cell_bold"]),
        Paragraph("Проблем", styles["cell_bold"]),
        Paragraph("Сумма тяжести", styles["cell_bold"]),
        Paragraph("Средняя тяжесть", styles["cell_bold"]),
        Paragraph("Ключевые проблемы", styles["cell_bold"]),
    ]
    rows = [header]

    for _, row in top10.iterrows():
        rank = int(row.get("ранг", 0))
        rows.append([
            Paragraph(str(rank), styles["cell"]),
            Paragraph(str(row["район"]), styles["cell"]),
            Paragraph(str(int(row["количество_проблем"])), styles["cell"]),
            Paragraph(str(int(row["сумма_тяжести"])), styles["cell"]),
            Paragraph(f"{float(row['средняя_тяжесть']):.1f}", styles["cell"]),
            Paragraph(str(row.get("ключевые_проблемы", ""))[:120], styles["cell"]),
        ])

    table = Table(
        rows,
        colWidths=[1 * cm, 4.2 * cm, 1.5 * cm, 2 * cm, 2 * cm, 5.5 * cm],
        repeatRows=1,
    )
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_commands.append(("BACKGROUND", (0, i), (-1, i), COLOR_ROW_ALT))

    table.setStyle(TableStyle(style_commands))
    return [
        Paragraph("ТОП-10 проблемных районов", styles["section"]),
        Spacer(1, 4),
        table,
        Spacer(1, 12),
    ]


def _llm_section(
    styles: dict[str, ParagraphStyle],
    llm_rows: list[dict],
) -> list:
    if not llm_rows:
        return []

    elements = [
        Paragraph("Аналитические выводы (ИИ)", styles["section"]),
        Spacer(1, 4),
    ]
    for item in llm_rows:
        district = item.get("район", "")
        desc = item.get("описание_llm") or item.get("описание", "")
        if not desc:
            continue
        elements.append(Paragraph(f"<b>{district}</b>", styles["district_name"]))
        elements.append(Paragraph(str(desc), styles["body"]))
        elements.append(Spacer(1, 6))
    return elements


def generate_leadership_pdf(
    stats: pd.DataFrame,
    total_rows: int,
    total_problems: int,
    output_path: str | Path,
    llm_rows: list[dict] | None = None,
    generated_at: datetime | None = None,
    total_input: int | None = None,
    avg_severity: float | None = None,
) -> Path:
    """Сформировать PDF-справку по статистике районов."""
    register_fonts()
    generated_at = generated_at or datetime.now()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = _styles()
    top10 = stats.head(10).copy()
    top3 = stats.head(3).copy()
    if not top10.empty and "ранг" not in top10.columns:
        top10.insert(0, "ранг", range(1, len(top10) + 1))
    if not top3.empty and "ранг" not in top3.columns:
        top3.insert(0, "ранг", range(1, len(top3) + 1))

    problem_share = (total_problems / total_rows * 100) if total_rows else 0.0
    story: list = []

    story.extend(_header_block(styles, generated_at))
    story.append(_kpi_cards(
        styles,
        total_rows,
        total_problems,
        len(stats),
        problem_share,
        total_input,
        avg_severity,
    ))
    story.append(Spacer(1, 14))
    story.extend(_top3_cards(styles, top3))
    story.extend(_top10_table(styles, top10))
    story.extend(_llm_section(styles, llm_rows or []))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Документ сформирован автоматически системой «ГородОК» на основе анализа обращений граждан.",
        styles["footer"],
    ))

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title="Справка по проблемным районам",
        author="ГородОК",
    )
    doc.build(story)
    return output_path


def generate_pdf_from_report_xlsx(
    xlsx_path: str | Path,
    pdf_path: str | Path | None = None,
) -> Path:
    """Пересобрать PDF из готового report.xlsx (после гибридного режима)."""
    xlsx_path = Path(xlsx_path)
    pdf_path = Path(pdf_path) if pdf_path else xlsx_path.with_suffix(".pdf")

    overview = pd.read_excel(xlsx_path, sheet_name="Обзор")
    top10 = pd.read_excel(xlsx_path, sheet_name="Топ-10")
    all_districts = pd.read_excel(xlsx_path, sheet_name="Все районы")

    row = overview.iloc[0]
    if "отобрано_к_анализу" in overview.columns:
        total_rows = int(row["отобрано_к_анализу"])
        total_input = int(row["всего_в_файле"])
    else:
        total_rows = int(row["всего_обращений"])
        total_input = None
    total_problems = int(row["выявлено_проблем"])
    avg_severity = float(row["средняя_тяжесть"]) if "средняя_тяжесть" in overview.columns else None

    llm_rows: list[dict] = []
    if "описание_llm" in top10.columns:
        for _, row in top10.iterrows():
            desc = row.get("описание_llm")
            if pd.notna(desc) and str(desc).strip():
                llm_rows.append({"район": row["район"], "описание_llm": str(desc)})

    return generate_leadership_pdf(
        all_districts,
        total_rows,
        total_problems,
        pdf_path,
        llm_rows=llm_rows or None,
        total_input=total_input,
        avg_severity=avg_severity,
    )
