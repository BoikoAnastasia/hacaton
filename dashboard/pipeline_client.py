"""Связь дашборда с analyze/pipeline.py и отдельными этапами."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.config import (
    ANALYZE_DIR,
    PROJECT_ROOT,
    REPORTS_DIR,
    UPLOADS_DIR,
    VENV_PYTHON,
)
from pipeline_options import DEFAULT_PRESET, PipelineOptions

DEFAULT_OPTIONS = PipelineOptions()


@dataclass
class AnalysisResult:
    ok: bool
    report_dir: Path | None
    cleaned: Path | None
    result: Path | None
    report: Path | None
    summary: Path | None
    log: str
    cleaning_stats: Path | None = None
    error: str | None = None
    preset: str = DEFAULT_PRESET


def child_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8:replace"
    env["PYTHONUTF8"] = "1"
    env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    env["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
    env["TQDM_DISABLE"] = "1"
    return env


def save_upload(uploaded_bytes: bytes, original_name: str) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = UPLOADS_DIR / f"{stamp}_{Path(original_name).name}"
    path.write_bytes(uploaded_bytes)
    return path


def publish_to_dashboard(result: AnalysisResult) -> None:
    """Копия отчётов в dashboard/data/reports/ для UI."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    for src in (
        result.result,
        result.report,
        result.summary,
        result.cleaned,
        result.cleaning_stats,
    ):
        if src and Path(src).exists():
            shutil.copy2(src, REPORTS_DIR / Path(src).name)


def _run_subprocess(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=child_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, log


def _report_context() -> tuple[Path, dict[str, Path]]:
    sys.path.insert(0, str(ANALYZE_DIR))
    from report_paths import plan_report_dir, report_files

    report_dir = plan_report_dir(PROJECT_ROOT)
    return report_dir, report_files(report_dir)


def _failure(
    report_dir: Path,
    paths: dict[str, Path],
    log: str,
    error: str,
    preset: str,
) -> AnalysisResult:
    return AnalysisResult(
        ok=False,
        report_dir=report_dir if report_dir.exists() else None,
        cleaned=paths["cleaned"] if paths["cleaned"].exists() else None,
        result=paths["result"] if paths["result"].exists() else None,
        report=paths["report"] if paths["report"].exists() else None,
        summary=paths["summary"] if paths["summary"].exists() else None,
        cleaning_stats=paths["cleaning_stats"] if paths["cleaning_stats"].exists() else None,
        log=log,
        error=error,
        preset=preset,
    )


def build_pipeline_cmd(input_path: Path, report_dir: Path, options: PipelineOptions) -> list[str]:
    """Аргументы для analyze/pipeline.py по выбранному пресету."""
    cmd = [
        str(VENV_PYTHON),
        str(ANALYZE_DIR / "pipeline.py"),
        "--input", str(input_path),
        "--work-dir", str(PROJECT_ROOT),
        "--output-dir", str(report_dir),
        "--batch-size", str(options.batch_size),
    ]

    if options.preset == "fast":
        cmd.extend(["--mode", "fast"])
    elif options.preset == "hybrid":
        cmd.extend(["--mode", "hybrid"])
    elif options.preset == "cluster":
        cmd.extend(["--mode", "cluster", "--clusters", str(options.clusters)])
    elif options.preset == "llm":
        cmd.extend(["--mode", "llm"])
    else:  # cluster_turbo
        cmd.extend([
            "--mode", "cluster",
            "--clusters", str(options.clusters),
            "--turbo",
        ])

    if options.limit > 0:
        cmd.extend(["--limit", str(options.limit)])
        if options.random_sample:
            cmd.append("--random")

    return cmd


def run_clean_only(input_path: Path, options: PipelineOptions) -> AnalysisResult:
    """Только excel.py — очистка без анализа."""
    report_dir, paths = _report_context()
    report_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(VENV_PYTHON),
        str(ANALYZE_DIR / "excel.py"),
        "--input", str(input_path),
        "--output", str(paths["cleaned"]),
    ]
    code, log = _run_subprocess(cmd, PROJECT_ROOT)
    if code != 0:
        return _failure(report_dir, paths, log, f"Очистка завершилась с кодом {code}", options.preset)

    result = AnalysisResult(
        ok=True,
        report_dir=report_dir,
        cleaned=paths["cleaned"],
        result=None,
        report=None,
        summary=None,
        cleaning_stats=paths["cleaning_stats"] if paths["cleaning_stats"].exists() else None,
        log=log,
        preset=options.preset,
    )
    if paths["cleaned"].exists():
        shutil.copy2(paths["cleaned"], REPORTS_DIR / "cleaned.xlsx")
    if result.cleaning_stats and result.cleaning_stats.exists():
        shutil.copy2(result.cleaning_stats, REPORTS_DIR / "cleaning_stats.json")
    return result


def run_analysis(input_path: Path, options: PipelineOptions | None = None) -> AnalysisResult:
    """Запуск выбранного режима обработки Excel."""
    options = options or DEFAULT_OPTIONS

    if not VENV_PYTHON.exists():
        return AnalysisResult(
            ok=False,
            report_dir=None,
            cleaned=None,
            result=None,
            report=None,
            summary=None,
            log="",
            error=f"Python не найден: {VENV_PYTHON}. Выполните .\\setup.ps1",
            preset=options.preset,
        )

    if options.preset == "clean":
        return run_clean_only(input_path, options)

    report_dir, paths = _report_context()
    cmd = build_pipeline_cmd(input_path, report_dir, options)
    code, log = _run_subprocess(cmd, PROJECT_ROOT)

    if code != 0:
        return _failure(
            report_dir, paths, log,
            f"Пайплайн завершился с кодом {code}",
            options.preset,
        )

    analysis = AnalysisResult(
        ok=True,
        report_dir=report_dir,
        cleaned=paths["cleaned"],
        result=paths["result"],
        report=paths["report"],
        summary=paths["summary"],
        cleaning_stats=paths["cleaning_stats"],
        log=log,
        preset=options.preset,
    )
    publish_to_dashboard(analysis)
    return analysis
