import streamlit as st

def nav_button(label, page_name):
  is_active = st.session_state.page == page_name

  if is_active:
    st.markdown(
      f'<div class="nav-btn active">{label}</div>',
      unsafe_allow_html=True
    )
  else:
    if st.button(label, key=f"nav_{page_name}", use_container_width=True):
      st.session_state.page = page_name
      st.rerun()