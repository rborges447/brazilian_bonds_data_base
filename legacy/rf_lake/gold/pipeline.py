"""Gold pipeline: silver → SQLite (missing dates only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rf_lake.datasets import DatasetConfig, DatasetTask, get_dataset_config
from rf_lake.gold.load import gold_from_silver
from rf_lake.incremental import missing_dates_gold, silver_paths_for_dataset
from rf_lake.logging import get_logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rf_lake.silver.pipeline import SilverResult

logger = get_logger(__name__)


@dataclass
class GoldResult:
    name: str
    status: str  # success | skipped | error
    rows: int = 0
    persisted: bool = False
    dates_candidate: list[str] = field(default_factory=list)
    dates_loaded: list[str] = field(default_factory=list)
    error: str | None = None


def run_gold(
    name: str,
    silver_paths: list[Path],
    candidate_dates: list[str],
    end_date: str,
    config: DatasetConfig | None = None,
) -> GoldResult:
    cfg = config or get_dataset_config(name)
    dates_candidate = list(candidate_dates)
    dates_to_load = missing_dates_gold(cfg, end_date)

    if cfg.date_mode == "missing_dates" and not dates_to_load:
        logger.info("[%s] Gold skipped: no missing dates in SQLite", name)
        return GoldResult(
            name=name,
            status="skipped",
            dates_candidate=dates_candidate,
            dates_loaded=[],
        )

    if not silver_paths:
        logger.warning("[%s] Gold skipped: no silver parquet", name)
        return GoldResult(
            name=name,
            status="skipped",
            dates_candidate=dates_candidate,
            dates_loaded=[],
        )

    try:
        total_rows = 0
        any_persisted = False
        for silver_path in silver_paths:
            if not silver_path.is_file():
                continue
            rows, ok = gold_from_silver(
                name,
                silver_path,
                dates_filter=dates_to_load if cfg.date_mode == "missing_dates" else None,
            )
            total_rows += rows
            any_persisted = any_persisted or ok

        persisted = any_persisted and (total_rows > 0 or cfg.date_mode == "run_always")
        logger.info(
            "[%s] Gold: %s dates to load, %s rows, persisted=%s",
            name,
            len(dates_to_load),
            total_rows,
            persisted,
        )
        return GoldResult(
            name=name,
            status="success" if persisted else "failed",
            rows=total_rows,
            persisted=persisted,
            dates_candidate=dates_candidate,
            dates_loaded=dates_to_load,
        )
    except Exception as exc:
        logger.error("[%s] Gold error: %s", name, exc, exc_info=True)
        return GoldResult(
            name=name,
            status="error",
            dates_candidate=dates_candidate,
            error=str(exc),
        )


def run_gold_phase(
    tasks: list[DatasetTask],
    silver_results: dict[str, "SilverResult"],
    end_date: str,
) -> dict[str, GoldResult]:
    logger.info("=== Gold phase (%s datasets) ===", len(tasks))
    results: dict[str, GoldResult] = {}

    for task in tasks:
        silver = silver_results.get(task.name)
        if silver is None or silver.status == "error":
            results[task.name] = GoldResult(
                name=task.name,
                status="skipped",
                dates_candidate=task.dates,
                error=silver.error if silver else "silver missing",
            )
            continue

        silver_paths: list[Path] = []
        if silver.path and silver.path.is_file():
            silver_paths = [silver.path]
        else:
            silver_paths = silver_paths_for_dataset(task.name, task.dates)

        results[task.name] = run_gold(
            task.name,
            silver_paths,
            task.dates,
            end_date,
            config=task.config,
        )

    logger.info("=== Gold phase completed ===")
    return results
