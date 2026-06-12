import base64

import streamlit as st

from components.nav_button import nav_button
from components.report_history import render_report_history
from pipeline_client import run_analysis, save_upload
from pipeline_options import PRESETS, DEFAULT_PRESET, PipelineOptions


def _build_options() -> PipelineOptions:
    preset = st.session_state.get("processing_preset", DEFAULT_PRESET)
    return PipelineOptions(
        preset=preset,
        limit=int(st.session_state.get("processing_limit", 0) or 0),
        random_sample=bool(st.session_state.get("processing_random", False)),
        batch_size=int(st.session_state.get("processing_batch", 8) or 8),
        clusters=int(st.session_state.get("processing_clusters", 800) or 800),
    )


def sidebar():
    with st.sidebar:
        with open("./assets/icons/file-report.png", "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <div style="
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 20px;
            ">
                <img
                src="data:image/png;base64, {img_base64}"
                width="45"
                height="45"
                >
                <div style="
                font-size: 20px;
                font-weight: 700;
                color: white;
                text-align: center;
                ">
                Аналитика обращений граждан
                </div>
            </div>
            """, unsafe_allow_html=True)

        nav_button("Главная", "main")
        nav_button("Графики", "graphics")
        nav_button("Отчёты", "reports")
        nav_button("Сравнение", "compare")

        st.divider()

        render_report_history()

        st.divider()
        uploaded_file = st.file_uploader(
            "Загрузите Excel файл",
            type=["xlsx"],
            key="upload_excel",
        )

        preset_ids = list(PRESETS.keys())
        preset = st.selectbox(
            "Режим обработки",
            options=preset_ids,
            format_func=lambda k: PRESETS[k].label,
            key="processing_preset",
        )
        info = PRESETS[preset]
        st.caption(info.description)
        st.caption(f"⏱ {info.eta}" + (" · нужна GPU" if info.needs_gpu else " · GPU не нужна"))

        with st.expander("Дополнительные параметры"):
            st.number_input(
                "Количество строк (0 = весь файл)",
                min_value=0,
                max_value=500_000,
                value=0,
                step=100,
                key="processing_limit",
            )
            if st.session_state.get("processing_limit", 0) > 0:
                st.checkbox("Случайная выборка", key="processing_random")

            if info.uses_llm():
                st.number_input(
                    "Размер батча LLM",
                    min_value=1,
                    max_value=32,
                    value=8,
                    key="processing_batch",
                )

            if info.uses_clusters():
                st.number_input(
                    "Макс. кластеров (≈ вызовов LLM)",
                    min_value=50,
                    max_value=5000,
                    value=800,
                    step=50,
                    key="processing_clusters",
                )

        if st.button(
            "Запустить обработку",
            key="run_analysis",
            use_container_width=True,
        ):
            if uploaded_file is None:
                st.error("Сначала загрузите файл .xlsx")
            else:
                options = _build_options()
                saved = save_upload(uploaded_file.getvalue(), uploaded_file.name)
                spinner = (
                    "Очистка файла…"
                    if options.preset == "clean"
                    else f"Обработка ({PRESETS[options.preset].label})… Это может занять время."
                )
                with st.spinner(spinner):
                    result = run_analysis(saved, options)

                if result.ok:
                    report_path = str(result.report_dir.resolve())
                    st.session_state["last_report_dir"] = report_path
                    st.session_state["active_report_path"] = report_path
                    st.session_state["_force_history_sync"] = report_path
                    st.session_state["report_data_version"] = (
                        st.session_state.get("report_data_version", 0) + 1
                    )
                    st.session_state["last_preset"] = options.preset
                    if info.updates_dashboard:
                        st.success("Готово. Обновляем дашборд…")
                        st.rerun()
                    else:
                        st.success(f"Очистка завершена. Файл: `{result.cleaned}`")
                else:
                    st.error(result.error or "Ошибка обработки")
                    with st.expander("Лог"):
                        st.code(result.log or "(пусто)")

        if st.session_state.get("last_report_dir"):
            last = PRESETS.get(
                st.session_state.get("last_preset", DEFAULT_PRESET),
                PRESETS[DEFAULT_PRESET],
            )
            st.caption(f"Последний режим: **{last.label}**")
            st.caption(f"Папка: `{st.session_state['last_report_dir']}`")
