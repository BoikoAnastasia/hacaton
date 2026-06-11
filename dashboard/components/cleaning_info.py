import streamlit as st


def render_cleaning_info(stats: dict | None) -> None:
    if not stats:
        return

    total_input = stats.get("total_input", 0)
    total_after = stats.get("total_after_clean", 0)
    if total_input <= total_after:
        return

    with st.expander("Как отбирались обращения к анализу", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("В исходном файле", f"{total_input:,}".replace(",", " "))
        c2.metric("Пустой текст", stats.get("removed_empty", 0))
        c3.metric("Не «Решаемый»", stats.get("removed_by_type", 0))
        c4.metric("Уже закрытые", stats.get("removed_by_outcome", 0))

        st.caption(
            f"Дубликаты: {stats.get('removed_duplicates', 0)} · "
            f"**К анализу:** {total_after:,}".replace(",", " ")
        )

        types = stats.get("types_in_file") or {}
        if types:
            st.markdown("**Типы в исходном файле:**")
            type_lines = " · ".join(f"{name}: {count}" for name, count in types.items())
            st.caption(type_lines)
