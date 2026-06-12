"""Карточки сравнения отчётов."""

from __future__ import annotations

import streamlit as st

from core.report_compare import ReportSnapshot, pct_change, format_delta, format_pct


def _fmt_value(value: int | float, *, is_float: bool = False) -> str:
    if is_float:
        return f"{value:.2f}"
    return f"{int(value):,}".replace(",", " ")


def _delta_class(delta: float, *, higher_is_worse: bool) -> str:
    if delta == 0:
        return "compare-delta-neutral"
    if higher_is_worse:
        return "compare-delta-bad" if delta > 0 else "compare-delta-good"
    return "compare-delta-neutral"


def render_report_picks(first: ReportSnapshot, second: ReportSnapshot) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="compare-report-card">
          <div class="compare-report-label">Первый отчёт</div>
          <div class="compare-report-name">{first.label}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="compare-report-card">
          <div class="compare-report-label">Второй отчёт</div>
          <div class="compare-report-name">{second.label}</div>
        </div>
        """, unsafe_allow_html=True)


def render_metric_card(
    title: str,
    first_val: int | float,
    second_val: int | float,
    *,
    is_float: bool = False,
    higher_is_worse: bool = False,
) -> None:
    delta = second_val - first_val
    pct = pct_change(first_val, second_val)
    delta_cls = _delta_class(delta, higher_is_worse=higher_is_worse)

    st.markdown(f"""
    <div class="compare-metric-card">
      <div class="compare-metric-title">{title}</div>
      <div class="compare-metric-row">
        <div class="compare-metric-period">
          <span class="compare-metric-tag">Первый</span>
          <span class="compare-metric-num">{_fmt_value(first_val, is_float=is_float)}</span>
        </div>
        <div class="compare-metric-arrow">→</div>
        <div class="compare-metric-period">
          <span class="compare-metric-tag">Второй</span>
          <span class="compare-metric-num">{_fmt_value(second_val, is_float=is_float)}</span>
        </div>
      </div>
      <div class="compare-metric-delta {delta_cls}">
        {format_delta(delta, is_float=is_float)}
        <span class="compare-metric-pct">({format_pct(pct)})</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_summary_metrics(first: ReportSnapshot, second: ReportSnapshot) -> None:
    metrics = [
        ("Всего в исходном файле", first.total_in_file, second.total_in_file, False, False),
        ("Отобрано к анализу", first.analyzed, second.analyzed, False, False),
        ("Выявлено проблем", first.problems, second.problems, False, True),
        ("Районов с проблемами", first.districts_with_problems, second.districts_with_problems, False, True),
        ("Средняя тяжесть", first.avg_severity, second.avg_severity, True, True),
        ("Доля проблем, %", first.problem_share_pct, second.problem_share_pct, True, True),
    ]

    row1 = st.columns(3)
    row2 = st.columns(3)
    for col, (title, v1, v2, is_float, worse) in zip(row1 + row2, metrics):
        with col:
            render_metric_card(title, v1, v2, is_float=is_float, higher_is_worse=worse)


def render_insights(lines: list[str], *, kind: str) -> None:
    if not lines:
        return
    cls = "compare-insight-up" if kind == "up" else "compare-insight-down"
    items = "".join(f"<li>{line}</li>" for line in lines)
    st.markdown(f'<ul class="compare-insight-list {cls}">{items}</ul>', unsafe_allow_html=True)
