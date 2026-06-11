"""Пути и имена папок для результатов пайплайна."""

from datetime import datetime
from pathlib import Path

from export_names import (
    KIND_CLEANED,
    KIND_CLEANING_STATS,
    KIND_REPORT,
    KIND_RESULT,
    KIND_SUMMARY,
    export_path,
)


def make_report_dir_name(when: datetime | None = None) -> str:
    """Имя папки: «Отчет от дд.мм.гг - чч.мм» (точка вместо «:» в времени — ограничение Windows)."""
    when = when or datetime.now()
    return when.strftime("Отчет от %d.%m.%y - %H.%M")


def reports_root(base_dir: Path) -> Path:
    """Корень для папок «Отчет от …»."""
    return base_dir / "storage" / "output"


def plan_report_dir(base_dir: Path, when: datetime | None = None) -> Path:
    """Путь к папке отчёта без создания на диске."""
    return reports_root(base_dir) / make_report_dir_name(when)


def ensure_report_dir(report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def remove_if_empty(report_dir: Path) -> bool:
    if report_dir.is_dir() and not any(report_dir.iterdir()):
        report_dir.rmdir()
        return True
    return False


def make_report_dir(base_dir: Path, when: datetime | None = None) -> Path:
    """Создать папку отчёта (для обратной совместимости)."""
    return ensure_report_dir(plan_report_dir(base_dir, when))


def report_files(report_dir: Path) -> dict[str, Path]:
    return {
        KIND_CLEANED: export_path(report_dir, KIND_CLEANED),
        KIND_RESULT: export_path(report_dir, KIND_RESULT),
        KIND_REPORT: export_path(report_dir, KIND_REPORT),
        KIND_SUMMARY: export_path(report_dir, KIND_SUMMARY),
        KIND_CLEANING_STATS: report_dir / "cleaning_stats.json",
    }
