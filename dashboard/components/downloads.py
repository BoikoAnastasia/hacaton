import streamlit as st

from core.report_context import get_active_report_dir
from core.report_files import (
    DOWNLOAD_KINDS,
    ZIP_EXTRA_KINDS,
    download_filename,
    find_report_file,
    zip_download_name,
)
from utils.make_zip import make_zip

DOWNLOAD_LABELS = {
    "result": "Полный Excel",
    "report": "Топ-10 Excel",
    "summary": "Справка PDF",
}

DOWNLOAD_MIME = {
    "summary": "application/pdf",
}


def render_download_buttons(*, key_prefix: str = "dl") -> None:
    base_dir = get_active_report_dir()
    available = []
    for kind in DOWNLOAD_KINDS:
        path = find_report_file(kind)
        if path and path.exists():
            available.append((kind, path))

    if not available:
        st.info("В выбранном отчёте нет файлов для скачивания.")
        return

    col1, col2, col3, col4 = st.columns(4)

    for col, kind in zip((col1, col2, col3), DOWNLOAD_KINDS):
        label = DOWNLOAD_LABELS[kind]
        path = find_report_file(kind)
        with col:
            if path and path.exists():
                mime = DOWNLOAD_MIME.get(kind)
                with open(path, "rb") as f:
                    kwargs = {
                        "label": label,
                        "data": f,
                        "file_name": download_filename(kind),
                        "key": f"{key_prefix}_{kind}",
                    }
                    if mime:
                        kwargs["mime"] = mime
                    st.download_button(**kwargs)
            else:
                st.button(
                    f"{label} — нет",
                    disabled=True,
                    use_container_width=True,
                    key=f"{key_prefix}_{kind}_missing",
                    help="Файл отсутствует в этой папке (старый отчёт).",
                )

    zip_items = list(available)
    for kind in ZIP_EXTRA_KINDS:
        path = find_report_file(kind)
        if path and path.exists():
            zip_items.append((kind, path))

    zip_paths = [path for _, path in zip_items]
    zip_names = [download_filename(kind) for kind, _ in zip_items]
    with col4:
        if len(zip_paths) > 1:
            st.download_button(
                "Скачать всё",
                data=make_zip(zip_paths, zip_names),
                file_name=zip_download_name(),
                mime="application/zip",
                key=f"{key_prefix}_zip",
            )
        elif len(zip_paths) == 1:
            st.button(
                "Скачать всё",
                disabled=True,
                use_container_width=True,
                key=f"{key_prefix}_zip_empty",
                help="Нужно минимум два файла для архива.",
            )


def columns_dowload_buttons():
    render_download_buttons(key_prefix="main")
