import streamlit as st
import base64


def _format_metric(value):
    if isinstance(value, float) and value != int(value):
        return str(value)
    if isinstance(value, (int, float)):
        return f"{int(value):,}".replace(",", " ")
    return str(value)


def render_kpi_cards(kpi):
  col1, col2, col3, col4 = st.columns(4)

  analyzed = kpi.get("analyzed", kpi["total"])
  total_subtitle = (
    f"Нерешённых к анализу: {_format_metric(analyzed)}"
    if analyzed != kpi["total"]
    else None
  )

  problem_subtitle = None
  if analyzed and kpi["problem_count"] != analyzed:
    share = round(kpi["problem_count"] / analyzed * 100, 1)
    problem_subtitle = f"{share}% от отобранных"

  cards = [
    ("./assets/icons/message.png", "Всего обращений", _format_metric(kpi["total"]), total_subtitle),
    ("./assets/icons/alert-triangle.png", "Выявлено проблем", _format_metric(kpi["problem_count"]), problem_subtitle),
    ("./assets/icons/star.png", "Районов с проблемами", _format_metric(kpi["districts_with_problems"]), None),
    ("./assets/icons/apartment.png", "Средняя тяжесть", kpi["avg_severity"], None),
  ]

  for col, (icon, title, value, subtitle) in zip([col1, col2, col3, col4], cards):
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
            {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
          </div>
        </div>
      """, unsafe_allow_html=True)