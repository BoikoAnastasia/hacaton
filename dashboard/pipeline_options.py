"""Режимы обработки Excel для дашборда и CLI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessingPreset:
    id: str
    label: str
    description: str
    eta: str
    needs_gpu: bool
    updates_dashboard: bool

    def uses_llm(self) -> bool:
        return self.id in ("hybrid", "cluster_turbo", "cluster", "llm")

    def uses_clusters(self) -> bool:
        return self.id in ("cluster_turbo", "cluster")


PRESETS: dict[str, ProcessingPreset] = {
    "clean": ProcessingPreset(
        id="clean",
        label="Только очистка",
        description="Фильтрация, нормализация текста, дедупликация. Без анализа и отчёта.",
        eta="1–3 мин",
        needs_gpu=False,
        updates_dashboard=False,
    ),
    "fast": ProcessingPreset(
        id="fast",
        label="Быстрый (правила)",
        description="Проблема и серьёзность по ключевым словам. Без нейросети, Top-3/Top-10.",
        eta="2–5 мин",
        needs_gpu=False,
        updates_dashboard=True,
    ),
    "hybrid": ProcessingPreset(
        id="hybrid",
        label="Гибридный",
        description="Быстрые правила + LLM-описание топовых районов в отчёте.",
        eta="5–15 мин",
        needs_gpu=True,
        updates_dashboard=True,
    ),
    "cluster_turbo": ProcessingPreset(
        id="cluster_turbo",
        label="Кластерный + turbo (рекомендуется)",
        description="Кластеризация по темам, LLM на представителях (~800 вызовов). Основной режим.",
        eta="10–25 мин",
        needs_gpu=True,
        updates_dashboard=True,
    ),
    "cluster": ProcessingPreset(
        id="cluster",
        label="Кластерный полный",
        description="Как turbo, но без ускорения: больше вызовов LLM, summary от модели.",
        eta="45–90 мин",
        needs_gpu=True,
        updates_dashboard=True,
    ),
    "llm": ProcessingPreset(
        id="llm",
        label="Полный LLM (каждая строка)",
        description="Qwen на каждое обращение. Максимальное качество, очень долго на больших файлах.",
        eta="часы–дни",
        needs_gpu=True,
        updates_dashboard=True,
    ),
}

DEFAULT_PRESET = "cluster_turbo"


@dataclass
class PipelineOptions:
    preset: str = DEFAULT_PRESET
    limit: int = 0
    random_sample: bool = False
    batch_size: int = 8
    clusters: int = 800

    def preset_info(self) -> ProcessingPreset:
        return PRESETS.get(self.preset, PRESETS[DEFAULT_PRESET])

    def uses_llm(self) -> bool:
        return self.preset in ("hybrid", "cluster_turbo", "cluster", "llm")

    def uses_clusters(self) -> bool:
        return self.preset in ("cluster_turbo", "cluster")
