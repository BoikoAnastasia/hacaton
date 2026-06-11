import streamlit as st


def nav_button(label, page_name):
    is_active = st.session_state.page == page_name

    if st.button(
        label,
        key=f"nav_{page_name}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
        disabled=is_active,
    ):
        st.session_state.page = page_name
        st.rerun()
