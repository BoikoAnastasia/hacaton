import streamlit as st
import html
import pandas as pd

from utils.cleaner import clean

def create_table(df, limit=None, show_full_table_button=False):
    # Оставляем только проблемные обращения
    df = df[df["Проблема"] == True]

    # Сортируем по серьёзности
    df = df.sort_values(by="Серьёзность", ascending=False)

    if limit is not None:
        df = df.head(limit)

    # Подготавливаем данные
    table_data = []

    table_height = min(
      700,
      len(df) * 55 + 120
    )
    
    for _, row in df.iterrows():
        severity = int(row["Серьёзность"])
        theme = html.escape(str(row["Группа тем"]))
        essence = html.escape(str(row["Суть проблемы"])).replace('\n', ' ').replace('\r', ' ')[:200]
        
        # Преобразуем дату в ISO формат для корректной сортировки
        date_obj = pd.to_datetime(row["Дата создания"])
        date_iso = date_obj.isoformat()  # формат: 2025-12-24T21:29:05
        date_display = date_obj.strftime("%d.%m.%Y %H:%M")  # формат: 24.12.2025 21:29
        
        parts = [
            clean(row["Населенный пункт"]),
            clean(row["Улица"]),
            clean(row["Дом"])
        ]
        parts = [p for p in parts if p]
        address = ", ".join(parts) if parts else "—"
        
        # Генерируем точки
        if severity <= 1:
            active_color = "#22C55E"
            inactive_color = "#166534"
        elif severity <= 3:
            active_color = "#F59E0B"
            inactive_color = "#78350F"
        else:
            active_color = "#EF4444"
            inactive_color = "#7F1D1D"
        
        dots = ""
        for i in range(5):
            color = active_color if i < severity else inactive_color
            dots += f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{color};margin-right:4px;"></span>'
        
        table_data.append({
            "date_iso": date_iso,
            "date_display": date_display,
            "theme": theme,
            "essence": essence,
            "severity_value": severity,
            "severity_dots": dots,
            "address": address
        })
    
    # Создаём HTML с JS сортировкой (исправленный)
    html_code = f"""
    <div class="essence-card">
        <div class="essence-title">
            Таблица извлечения сути обращений
            <span style="font-size: 14px; font-weight: normal; margin-left: 10px;">
                (Нажмите на заголовок для сортировки)
            </span>
        </div>
        <div style="max-height: 700px; overflow-y: auto; border-radius: 10px;">
            <table class="essence-table" id="sortableTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)" data-type="date">Дата обращения <span class="sort-arrow">▼</span></th>
                        <th onclick="sortTable(1)" data-type="string">Тема <span class="sort-arrow">↕</span></th>
                        <th onclick="sortTable(2)" data-type="string">Суть обращения <span class="sort-arrow">↕</span></th>
                        <th onclick="sortTable(3)" data-type="number">Тяжесть <span class="sort-arrow">↕</span></th>
                        <th onclick="sortTable(4)" data-type="string">Адрес <span class="sort-arrow">↕</span></th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    {''.join([f'''
                    <tr>
                        <td data-date="{item['date_iso']}">{item['date_display']}</td>
                        <td>{item['theme']}</td>
                        <td>{item['essence']}</td>
                        <td data-value="{item['severity_value']}">{item['severity_dots']}</td>
                        <td>{item['address']}</td>
                    </tr>
                    ''' for item in table_data])}
                </tbody>
            </table>
        </div>
    </div>
    
    <style>
    .essence-card {{
        background: #111827;
        border: 1px solid #374151;
        border-radius: 18px;
        padding: 24px;
        margin-top: 20px;
    }}
    .essence-title {{
        font-size: 24px;
        font-weight: 700;
        color: white;
        margin-bottom: 20px;
    }}
    .essence-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .essence-table th {{
        background: #1F2937;
        text-align: left;
        padding: 14px;
        color: white;
        cursor: pointer;
        user-select: none;
        position: sticky;
        top: 0;
    }}
    .essence-table th:hover {{
        background: #374151;
    }}
    .essence-table td {{
        padding: 14px;
        border-top: 1px solid #374151;
        color: #D1D5DB;
    }}
    .sort-arrow {{
        margin-left: 8px;
        font-size: 12px;
        opacity: 0.5;
    }}
    </style>
    
    <script>
    let sortColumn = 0;
    let sortAscending = false;
    
    function sortTable(column) {{
        const tbody = document.getElementById('tableBody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        if (sortColumn === column) {{
            sortAscending = !sortAscending;
        }} else {{
            sortColumn = column;
            sortAscending = true;
        }}
        
        rows.sort((a, b) => {{
            let aVal, bVal;
            const type = document.querySelectorAll('th')[column].getAttribute('data-type');
            
            if (type === 'date') {{
                aVal = new Date(a.cells[0].getAttribute('data-date') || a.cells[0].textContent);
                bVal = new Date(b.cells[0].getAttribute('data-date') || b.cells[0].textContent);
                return sortAscending ? aVal - bVal : bVal - aVal;
            }} else if (type === 'number') {{
                aVal = parseInt(a.cells[3].getAttribute('data-value')) || 0;
                bVal = parseInt(b.cells[3].getAttribute('data-value')) || 0;
                return sortAscending ? aVal - bVal : bVal - aVal;
            }} else {{
                aVal = a.cells[column].textContent.toLowerCase();
                bVal = b.cells[column].textContent.toLowerCase();
                return sortAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }}
        }});
        
        rows.forEach(row => tbody.appendChild(row));
        
        // Обновляем стрелки
        const arrows = document.querySelectorAll('.sort-arrow');
        arrows.forEach(arrow => {{
            arrow.textContent = '↕';
            arrow.style.opacity = '0.5';
        }});
        
        const activeArrow = document.querySelectorAll('th')[column].querySelector('.sort-arrow');
        activeArrow.textContent = sortAscending ? '▼' : '▲';
        activeArrow.style.opacity = '1';
    }}
    </script>
    """
    
    st.components.v1.html(html_code, height=table_height)
    
    if show_full_table_button:
      button_key = "view_full_table"
      # Добавляем стили динамически для конкретной кнопки по её key
      st.markdown(f"""
      <style>
      div[data-testid="stElementContainer"][class*="{button_key}"] button {{
        background-color: var(--button);
        width: 100%;
        border: none;
        border-radius: 10px;
        padding: 10px;
        color: white;
        font-weight: 500;
      }}
      div[data-testid="stElementContainer"][class*="{button_key}"] button:hover {{
          opacity: 0.8;
      }}
      </style>
      """, unsafe_allow_html=True)
      
      if st.button("Смотреть всю таблицу", use_container_width=True, key=button_key):
        st.session_state.page = "reports"
        st.rerun()