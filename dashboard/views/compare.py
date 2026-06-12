from pathlib import Path

import pandas as pd
import streamlit as st

from components.compare_cards import (
    render_insights,
    render_report_picks,
    render_summary_metrics,
)
from core.report_compare import (
    compare_districts,
    comparison_warning,
    format_pct,
    load_districts,
    load_report_snapshot,
)
from core.report_store import list_saved_reports
from utils.compare_pdf_export import build_comparison_pdf


def _report_options() -> dict[str, str]:
    return {str(item.path.resolve()): item.label for item in list_saved_reports()}


def _style_delta(val, *, higher_is_worse: bool = True) -> str:
    if pd.isna(val):
        return "color: #9ca3af"
    try:
        num = float(val)
    except (TypeError, ValueError):
        return "color: #9ca3af"
    if num == 0:
        return "color: #9ca3af"
    if higher_is_worse:
        color = "#f87171" if num > 0 else "#4ade80"
    else:
        color = "#9ca3af"
    return f"color: {color}; font-weight: 600"


def _styled_district_table(table: pd.DataFrame):
    display = table.rename(columns={
        "район": "Район",
        "проблем_1": "Проблем (первый)",
        "проблем_2": "Проблем (второй)",
        "тяжесть_1": "Тяжесть (первый)",
        "тяжесть_2": "Тяжесть (второй)",
    }).copy()

    for col in ("Проблем (первый)", "Проблем (второй)", "Δ проблем"):
        display[col] = display[col].astype(int)

    display["Δ проблем, %"] = display["Δ проблем, %"].apply(
        lambda v: format_pct(v) if pd.notna(v) else "н/д",
    )
    display["Δ тяжести, %"] = display["Δ тяжести, %"].apply(
        lambda v: format_pct(v) if pd.notna(v) else "н/д",
    )

    styled = display.style.map(
        lambda v: _style_delta(v),
        subset=["Δ проблем"],
    ).map(
        lambda v: _style_delta(v),
        subset=["Δ тяжести"],
    )

    return styled, display


def render_compare():
    st.subheader("Сравнение отчётов")

    options = _report_options()
    if len(options) < 2:
        st.info("Нужно минимум два сохранённых отчёта в `storage/output`.")
        return

    paths = list(options.keys())
    default_first = paths[1] if len(paths) > 1 else paths[0]
    default_second = paths[0]

    pick_col1, pick_col2 = st.columns(2)
    with pick_col1:
        first_path = st.selectbox(
            "Первый отчёт",
            paths,
            index=paths.index(default_first) if default_first in paths else 0,
            format_func=lambda p: options[p],
            key="compare_first_report",
        )
    with pick_col2:
        second_path = st.selectbox(
            "Второй отчёт",
            paths,
            index=paths.index(default_second) if default_second in paths else 0,
            format_func=lambda p: options[p],
            key="compare_second_report",
        )

    if first_path == second_path:
        st.warning("Выберите два разных отчёта.")
        return

    first = load_report_snapshot(Path(first_path))
    second = load_report_snapshot(Path(second_path))
    if not first or not second:
        st.error("Не удалось прочитать один из отчётов (нужен файл «… — топ районов.xlsx»).")
        return

    warning = comparison_warning(first, second)
    if warning:
        st.warning(warning)

    render_report_picks(first, second)

    st.markdown("#### Сводные показатели")
    render_summary_metrics(first, second)

    first_districts = load_districts(first.path)
    second_districts = load_districts(second.path)
    if first_districts is None or second_districts is None:
        st.info("Таблица по районам недоступна для одного из отчётов.")
        return

    st.markdown("#### Изменения по районам")
    table = compare_districts(first_districts, second_districts)
    styled, _ = _styled_district_table(table)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Проблем (первый)": st.column_config.NumberColumn(format="%d"),
            "Проблем (второй)": st.column_config.NumberColumn(format="%d"),
            "Δ проблем": st.column_config.NumberColumn(format="%+d"),
            "Тяжесть (первый)": st.column_config.NumberColumn(format="%.2f"),
            "Тяжесть (второй)": st.column_config.NumberColumn(format="%.2f"),
            "Δ тяжести": st.column_config.NumberColumn(format="%+.2f"),
        },
    )

    top_up = table[table["Δ проблем"] > 0].head(3)
    top_down = table[table["Δ проблем"] < 0].head(3)

    if not top_up.empty or not top_down.empty:
        st.markdown("#### Кратко")
        if not top_up.empty:
            st.caption("Рост числа проблем")
            render_insights([
                f"<b>{row['район']}</b>: +{int(row['Δ проблем'])} "
                f"({format_pct(row['Δ проблем, %'])})"
                for _, row in top_up.iterrows()
            ], kind="up")
        if not top_down.empty:
            st.caption("Снижение числа проблем")
            render_insights([
                f"<b>{row['район']}</b>: {int(row['Δ проблем'])} "
                f"({format_pct(row['Δ проблем, %'])})"
                for _, row in top_down.iterrows()
            ], kind="down")

    st.markdown('<div class="compare-download-wrap">', unsafe_allow_html=True)
    st.divider()
    pdf_bytes, pdf_name = build_comparison_pdf(first, second, table)
    st.download_button(
        "Скачать сравнение (PDF)",
        data=pdf_bytes,
        file_name=pdf_name,
        mime="application/pdf",
        type="primary",
        use_container_width=True,
        key="compare_download_pdf",
    )
    st.markdown("</div>", unsafe_allow_html=True)
