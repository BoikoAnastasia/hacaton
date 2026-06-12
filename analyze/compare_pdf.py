"""PDF-отчёт с результатами сравнения двух отчётов."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from pdf_report import (
    COLOR_BORDER,
    COLOR_HEADER_BG,
    COLOR_PRIMARY,
    COLOR_ROW_ALT,
    _styles,
    register_fonts,
)


def _fmt_int(value: int | float) -> str:
    return f"{int(value):,}".replace(",", " ")


def _fmt_val(value: int | float, *, is_float: bool) -> str:
    return f"{value:.2f}" if is_float else _fmt_int(value)


def _pct_change(first: float, second: float) -> float | None:
    if first == 0:
        return 0.0 if second == 0 else None
    return round((second - first) / first * 100, 1)


def _format_pct(pct: float | None) -> str:
    return "н/д" if pct is None else f"{pct:+.1f}%"


def _delta_html(
    first: float,
    second: float,
    *,
    is_float: bool = False,
    higher_is_worse: bool = False,
) -> str:
    delta = second - first
    pct = _pct_change(first, second)
    if is_float:
        delta_txt = f"{delta:+.2f}"
    else:
        delta_txt = f"{delta:+,.0f}".replace(",", " ")

    if delta == 0:
        color = "#9CA3AF"
    elif higher_is_worse:
        color = "#EF4444" if delta > 0 else "#22C55E"
    else:
        color = "#9CA3AF"

    return f'<font color="{color}"><b>{delta_txt}</b> ({_format_pct(pct)})</font>'


def _header(styles: dict[str, ParagraphStyle], generated_at: datetime) -> list:
    block = Table([[
        Paragraph("ГородОК", styles["title"]),
        Paragraph(
            "Сравнение отчётов<br/>"
            f"<font color='#9CA3AF'>Сформировано: {generated_at.strftime('%d.%m.%Y %H:%M')}</font>",
            styles["subtitle"],
        ),
    ]], colWidths=[8 * cm, 9.5 * cm])
    block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    return [block, Spacer(1, 12)]


def _report_names_block(
    styles: dict[str, ParagraphStyle],
    first_label: str,
    second_label: str,
) -> Table:
    data = [[
        Paragraph(
            f"<font color='#9CA3AF'>Первый отчёт</font><br/><b>{first_label}</b>",
            styles["body"],
        ),
        Paragraph(
            f"<font color='#9CA3AF'>Второй отчёт</font><br/><b>{second_label}</b>",
            styles["body"],
        ),
    ]]
    table = Table(data, colWidths=[8.75 * cm, 8.75 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def _metrics_table(
    styles: dict[str, ParagraphStyle],
    metrics: list[tuple[str, float, float, bool, bool]],
) -> Table:
    header = [
        Paragraph("Показатель", styles["cell_bold"]),
        Paragraph("Первый", styles["cell_bold"]),
        Paragraph("Второй", styles["cell_bold"]),
        Paragraph("Изменение", styles["cell_bold"]),
    ]
    rows = [header]
    for title, v1, v2, is_float, worse in metrics:
        rows.append([
            Paragraph(title, styles["cell"]),
            Paragraph(_fmt_val(v1, is_float=is_float), styles["cell"]),
            Paragraph(_fmt_val(v2, is_float=is_float), styles["cell"]),
            Paragraph(_delta_html(v1, v2, is_float=is_float, higher_is_worse=worse), styles["cell"]),
        ])

    table = Table(rows, colWidths=[5.5 * cm, 3.5 * cm, 3.5 * cm, 5 * cm], repeatRows=1)
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "ReportBold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            commands.append(("BACKGROUND", (0, i), (-1, i), COLOR_ROW_ALT))
    table.setStyle(TableStyle(commands))
    return table


def _districts_table(styles: dict[str, ParagraphStyle], districts: pd.DataFrame) -> Table:
    header = [
        Paragraph("Район", styles["cell_bold"]),
        Paragraph("П1", styles["cell_bold"]),
        Paragraph("П2", styles["cell_bold"]),
        Paragraph("Δ", styles["cell_bold"]),
        Paragraph("Δ%", styles["cell_bold"]),
        Paragraph("Тяж.1", styles["cell_bold"]),
        Paragraph("Тяж.2", styles["cell_bold"]),
    ]
    rows = [header]
    for _, row in districts.head(25).iterrows():
        pct = row.get("Δ проблем, %")
        pct_txt = _format_pct(pct) if pd.notna(pct) else "н/д"
        delta = int(row["Δ проблем"])
        if delta > 0:
            delta_html = f'<font color="#EF4444"><b>{delta:+d}</b></font>'
        elif delta < 0:
            delta_html = f'<font color="#22C55E"><b>{delta:+d}</b></font>'
        else:
            delta_html = "0"

        rows.append([
            Paragraph(str(row["район"])[:42], styles["cell"]),
            Paragraph(str(int(row["проблем_1"])), styles["cell"]),
            Paragraph(str(int(row["проблем_2"])), styles["cell"]),
            Paragraph(delta_html, styles["cell"]),
            Paragraph(pct_txt, styles["cell"]),
            Paragraph(f"{float(row['тяжесть_1']):.1f}", styles["cell"]),
            Paragraph(f"{float(row['тяжесть_2']):.1f}", styles["cell"]),
        ])

    table = Table(
        rows,
        colWidths=[4.8 * cm, 1.3 * cm, 1.3 * cm, 1.2 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm],
        repeatRows=1,
    )
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "ReportBold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            commands.append(("BACKGROUND", (0, i), (-1, i), COLOR_ROW_ALT))
    table.setStyle(TableStyle(commands))
    return table


def _insights_block(styles: dict[str, ParagraphStyle], districts: pd.DataFrame) -> list:
    elements: list = []
    top_up = districts[districts["Δ проблем"] > 0].head(3)
    top_down = districts[districts["Δ проблем"] < 0].head(3)
    if top_up.empty and top_down.empty:
        return elements

    elements.append(Paragraph("Краткие выводы", styles["section"]))
    for _, row in top_up.iterrows():
        pct = _format_pct(row["Δ проблем, %"]) if pd.notna(row["Δ проблем, %"]) else "н/д"
        elements.append(Paragraph(
            f'<font color="#EF4444"><b>Рост:</b></font> <b>{row["район"]}</b> — '
            f'+{int(row["Δ проблем"])} проблем ({pct})',
            styles["body"],
        ))
    for _, row in top_down.iterrows():
        pct = _format_pct(row["Δ проблем, %"]) if pd.notna(row["Δ проблем, %"]) else "н/д"
        elements.append(Paragraph(
            f'<font color="#22C55E"><b>Снижение:</b></font> <b>{row["район"]}</b> — '
            f'{int(row["Δ проблем"])} проблем ({pct})',
            styles["body"],
        ))
    return elements


def build_metrics_rows(first, second) -> list[tuple[str, float, float, bool, bool]]:
    return [
        ("Всего в исходном файле", first.total_in_file, second.total_in_file, False, False),
        ("Отобрано к анализу", first.analyzed, second.analyzed, False, False),
        ("Выявлено проблем", first.problems, second.problems, False, True),
        ("Районов с проблемами", first.districts_with_problems, second.districts_with_problems, False, True),
        ("Средняя тяжесть", first.avg_severity, second.avg_severity, True, True),
        ("Доля проблем, %", first.problem_share_pct, second.problem_share_pct, True, True),
    ]


def generate_comparison_pdf(
    first,
    second,
    districts: pd.DataFrame,
    *,
    generated_at: datetime | None = None,
) -> bytes:
    """Сформировать PDF (bytes) для скачивания из дашборда."""
    register_fonts()
    generated_at = generated_at or datetime.now()
    styles = _styles()

    story: list = []
    story.extend(_header(styles, generated_at))
    story.append(_report_names_block(styles, first.label, second.label))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Сводные показатели", styles["section"]))
    story.append(_metrics_table(styles, build_metrics_rows(first, second)))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Изменения по районам (топ-25)", styles["section"]))
    story.append(Spacer(1, 4))
    story.append(_districts_table(styles, districts))

    insights = _insights_block(styles, districts)
    if insights:
        story.append(Spacer(1, 12))
        story.extend(insights)

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Документ сформирован автоматически системой «ГородОК».",
        styles["footer"],
    ))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title="Сравнение отчётов",
        author="ГородОК",
    )
    doc.build(story)
    return buffer.getvalue()


def comparison_pdf_filename(first_label: str, second_label: str) -> str:
    name = f"Сравнение — {first_label} и {second_label}.pdf"
    return name.replace("/", "-").replace("\\", "-")[:180]
