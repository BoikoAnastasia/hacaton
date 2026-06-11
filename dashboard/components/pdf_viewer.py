from pathlib import Path

import streamlit as st


def render_pdf_viewer(pdf_path: Path, *, zoom: float = 2.0) -> None:
    """Просмотр PDF как страницы-картинки — без панели браузера."""
    try:
        import fitz  # pymupdf
    except ImportError:
        st.error("Для просмотра PDF установите: `pip install pymupdf`")
        return

    doc = fitz.open(pdf_path)
    matrix = fitz.Matrix(zoom, zoom)
    total = doc.page_count

    with st.container(border=True):
        for index, page in enumerate(doc, start=1):
            if total > 1:
                st.caption(f"Страница {index} из {total}")
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            st.image(pix.tobytes("png"), use_container_width=True)

    doc.close()
