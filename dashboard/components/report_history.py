from pathlib import Path

import streamlit as st

from core.report_context import normalize_report_path, paths_equal
from core.report_store import can_open_report, list_saved_reports


def _label_for(path: str, labels: dict[str, str]) -> str:
    return labels.get(path, Path(path).name)


def _init_active_report(entries) -> None:
    if st.session_state.get("active_report_path"):
        return
    if entries:
        st.session_state["active_report_path"] = str(entries[0].path.resolve())


def render_report_history() -> None:
    entries = list_saved_reports()
    if not entries:
        return

    st.markdown("**История отчётов**")
    _init_active_report(entries)

    paths = [str(entry.path.resolve()) for entry in entries]
    labels = {str(entry.path.resolve()): entry.label for entry in entries}

    active = st.session_state.get("active_report_path")
    if active:
        active = str(normalize_report_path(active))
        st.session_state["active_report_path"] = active

    forced = st.session_state.pop("_force_history_sync", None)
    if forced and forced in paths:
        st.session_state["report_history_select"] = forced
    elif "report_history_select" not in st.session_state:
        st.session_state["report_history_select"] = (
            active if active in paths else paths[0]
        )

    st.selectbox(
        "Сохранённые отчёты",
        options=paths,
        format_func=lambda p: _label_for(p, labels),
        key="report_history_select",
        label_visibility="collapsed",
    )

    pending = str(normalize_report_path(st.session_state["report_history_select"]) or "")
    is_active = paths_equal(pending, active)

    if st.button(
        "Выбрать",
        key="report_history_apply",
        use_container_width=True,
        type="primary" if not is_active else "secondary",
        disabled=is_active or not pending,
    ):
        if can_open_report(pending):
            st.session_state["active_report_path"] = pending
            st.session_state["report_data_version"] = (
                st.session_state.get("report_data_version", 0) + 1
            )
            st.rerun()
        else:
            st.error("В этой папке нет готового отчёта (нужен result.xlsx или report.xlsx).")

    if active and active in labels:
        st.caption(f"Сейчас на экране: **{labels[active]}**")
        st.caption("Графики, таблицы и кнопки «Скачать отчёты» — из этой папки.")
    else:
        st.caption("Выберите отчёт и нажмите «Выбрать».")

    entry = next((e for e in entries if str(e.path.resolve()) == pending), None)
    if entry and not entry.has_result:
        st.caption("Нет result.xlsx — на главной может не быть полной таблицы.")
