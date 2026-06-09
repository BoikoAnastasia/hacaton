"""Пересобрать dashboard из свежей папки хакатон (без затрагивания analyze/)."""
from __future__ import annotations

import shutil
from pathlib import Path

HACK = Path(__file__).resolve().parent.parent.parent
GORODOK = HACK / "gorodok"
FRONTEND_SRC = HACK / "хакатон"
DASHBOARD = GORODOK / "dashboard"


def ignore(dir_path, names):
    return {"__pycache__", ".git", "reports"} & set(names)


def main():
    if not FRONTEND_SRC.exists():
        raise SystemExit(f"Нет папки: {FRONTEND_SRC}")

    for sub in ("app.py", "charts.py", "analytics.py", "views", "components", "utils", "assets", "core"):
        src = FRONTEND_SRC / sub
        dst = DASHBOARD / sub
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=ignore)
        elif src.exists():
            shutil.copy2(src, dst)

    print("Скопирован UI из хакатон/. Заново примените pipeline_client.py и sidebar.py из репозитория.")


if __name__ == "__main__":
    main()
