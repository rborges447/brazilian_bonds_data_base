"""Daily bronze → silver → gold sync (extracted from CLI)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.cli.gold import _materialize_builder, _run_result
from app.config import get_settings
from app.lake.bronze.pipeline import run_bronze_phase
from app.lake.bronze.tasks import resolve_bronze_tasks
from app.lake.gold import GoldOrchestrator
from app.lake.gold.tasks import resolve_gold_tasks
from app.lake.silver.pipeline import run_silver_phase
from app.lake.silver.tasks import resolve_silver_tasks


@dataclass(frozen=True)
class SyncPhaseResult:
    name: str
    task_count: int
    details: Any


def _filter_tasks(tasks: list[Any], datasets: list[str] | None) -> list[Any]:
    if not datasets:
        return tasks
    allowed = set(datasets)
    return [t for t in tasks if t.name in allowed]


def run_daily_sync(
    end: str | None = None,
    *,
    start_date: str | None = None,
    persist: bool = True,
    datasets: list[str] | None = None,
) -> list[SyncPhaseResult]:
    """Run bronze, silver, and gold phases (same orchestration as ``sync cmd_daily``)."""
    get_settings().ensure_data_layout()

    bronze_tasks = _filter_tasks(resolve_bronze_tasks(end, start_date=start_date), datasets)
    bronze_results = run_bronze_phase(bronze_tasks)

    silver_tasks = _filter_tasks(resolve_silver_tasks(end, start_date=start_date), datasets)
    silver_results = run_silver_phase(silver_tasks)

    gold_tasks = _filter_tasks(resolve_gold_tasks(end, persist=persist, start_date=start_date), datasets)
    orch = GoldOrchestrator()
    gold_results: list[Any] = []
    for task in gold_tasks:
        if not task.dates and task.name != "feriados":
            continue
        result = _materialize_builder(orch, task.name, task.dates)
        _run_result(result, do_persist=persist)
        gold_results.append(result)

    return [
        SyncPhaseResult(name="bronze", task_count=len(bronze_tasks), details=bronze_results),
        SyncPhaseResult(name="silver", task_count=len(silver_tasks), details=silver_results),
        SyncPhaseResult(name="gold", task_count=len(gold_tasks), details=gold_results),
    ]
