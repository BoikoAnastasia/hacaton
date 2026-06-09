def render_top_district_card(
  rank,
  district,
  count,
  severity,
  problems
):
  color = "#EF4444" if severity >= 3.5 else "#F59E0B"

  if severity >= 4:
    color = "#EF4444" 
    bg_color = "#7F1D1D"
    border_color = "#EF4444"
  elif severity >= 3.5:
    color = "#F97316"
    bg_color = "#7C2D12"
    border_color = "#F97316"
  elif severity >= 2:
    color = "#F59E0B" 
    bg_color = "#78350F"
    border_color = "#F59E0B"
  else:
    color = "#22C55E" 
    bg_color = "#14532D"
    border_color = "#22C55E"

  problems_html = "".join(
      f"<li>{p}</li>"
      for p in problems[:3]
  )

  problems_html = "".join(
      f"<li>{p}</li>"
      for p in problems[:3]
  )

  return f"""
    <div class="district-card" style="border-left: 4px solid {border_color};">
      <div class="district-header">
        <div class="district-rank" style="background: {color};">
          {rank}
        </div>
        <div>
          <div class="district-name">
            {district}
          </div>
          <div class="district-count">
            {count} проблем
          </div>
        </div>
      </div>
      <div class="district-severity"
        style="color:{color}; border-color:{color};">
        Средняя тяжесть: {severity:.1f} / 5
      </div>
      <div class="district-problems-title">
        Ключевые проблемы:
      </div>
      <ul class="district-problems">
        {problems_html}
      </ul>
    </div>
  """