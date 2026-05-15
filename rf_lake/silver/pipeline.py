"""Silver pipeline: bronze → transform → data/silver (somente datas faltantes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rf_lake.bronze.pipeline import BronzeResult
from rf_lake.bronze.paths import silver_parquet
from rf_lake.datasets import DatasetTask
from rf_lake.incremental import missing_dates_silver, snapshot_key_dates
from rf_lake.logging import get_logger
from rf_lake.silver.run import silver_from_bronze
from rf_lake.watermarks import set_watermark

logger = get_logger(__name__)


@dataclass
class SilverResult:
    name: str
    status: str  # success | skipped | error
    path: Path | None = None
    rows: int = 0
    dates: list[str] = field(default_factory=list)
    dates_candidate: list[str] = field(default_factory=list)
    dates_processed: list[str] = field(default_factory=list)
    error: str | None = None


def run_silver(
    name: str,
    bronze_path: Path,
    candidate_dates: list[str],
) -> SilverResult:
    dates_candidate = list(candidate_dates)
    key = snapshot_key_dates(candidate_dates)

    if not bronze_path.is_file():
        logger.warning("[%s] Silver skipped: bronze inexistente %s", name, bronze_path)
        return SilverResult(
            name=name,
            status="skipped",
            dates_candidate=dates_candidate,
        )

    dates_to_run = missing_dates_silver(name, candidate_dates, bronze_path)

    if not dates_to_run:
        silver_path = silver_parquet(name, key)
        logger.info(
            "[%s] Silver skipped: %s candidatas, 0 faltantes",
            name,
            len(dates_candidate),
        )
        return SilverResult(
            name=name,
            status="skipped",
            path=silver_path if silver_path.is_file() else None,
            rows=0,
            dates=key if silver_path.is_file() else [],
            dates_candidate=dates_candidate,
            dates_processed=[],
        )

    try:
        path, rows, dates_processed = silver_from_bronze(name, bronze_path, dates_to_run)
        if rows > 0 and dates_processed:
            set_watermark(name, "silver", dates_processed)

        logger.info(
            "[%s] Silver: %s candidatas, %s com dados, %s linhas → %s",
            name,
            len(dates_candidate),
            len(dates_processed),
            rows,
            path,
        )
        return SilverResult(
            name=name,
            status="success",
            path=path,
            rows=rows,
            dates=dates_processed,
            dates_candidate=dates_candidate,
            dates_processed=dates_processed,
        )
    except Exception as exc:
        logger.error("[%s] Silver error: %s", name, exc, exc_info=True)
        return SilverResult(
            name=name,
            status="error",
            dates_candidate=dates_candidate,
            error=str(exc),
        )


def run_silver_phase(
    tasks: list[DatasetTask],
    bronze_results: dict[str, "BronzeResult"],
) -> dict[str, SilverResult]:
    logger.info("=== Silver phase (%s datasets) ===", len(tasks))
    results: dict[str, SilverResult] = {}

    for task in tasks:
        bronze = bronze_results.get(task.name)
        if bronze is None or bronze.status == "error":
            results[task.name] = SilverResult(
                name=task.name,
                status="skipped",
                dates_candidate=task.dates,
                error=bronze.error if bronze else "bronze ausente",
            )
            continue

        bronze_path = bronze.path
        if bronze_path is None or not bronze_path.is_file():
            key = snapshot_key_dates(task.dates)
            from rf_lake.incremental import bronze_artifact_path

            bronze_path = bronze_artifact_path(task.name, key)
            if not bronze_path.is_file():
                results[task.name] = SilverResult(
                    name=task.name,
                    status="skipped",
                    dates_candidate=task.dates,
                )
                continue

        candidate = task.dates if bronze.status == "skipped" else (bronze.dates or task.dates)
        results[task.name] = run_silver(task.name, bronze_path, candidate)

    logger.info("=== Silver phase concluída ===")
    return results
