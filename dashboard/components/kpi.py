import streamlit as st
import base64

def render_kpi_cards(kpi):
  col1, col2, col3, col4 = st.columns(4)

  cards = [
    ("./assets/icons/message.png", "Всего обращений", kpi["total"]),
    ("./assets/icons/alert-triangle.png", "Проблемных", kpi["problem_count"]),
    ("./assets/icons/star.png", "Муниципалитетов", kpi["municipalities"]),
    ("./assets/icons/apartment.png", "Средняя тяжесть", kpi["avg_severity"]),
  ]

  for col, (icon, title, value) in zip([col1, col2, col3, col4], cards):
    with col:
      # Конвертируем изображение в base64 прямо здесь
      with open(icon, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()

      st.markdown(f"""
        <div class="metric-card">
          <div class="metric-left">
            <div class="metric-icon">
              <img src="data:image/png;base64,{img_base64}" width="45" height="45">
            </div>
          </div>
          <div class="metric-right">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
          </div>
        </div>
      """, unsafe_allow_html=True)