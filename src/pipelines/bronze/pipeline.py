"""Bronze pipeline orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from config import get_settings
from models.datasets import DatasetTask
from pipelines.bronze.registry import extract_dataset

logger = logging.getLogger(__name__)


@dataclass
class BronzeResult:
    name: str
    status: str  # success | skipped | error
    path: Path | None = None
    row_count: int = 0
    segment_keys: list[str] = field(default_factory=list)
    dates_candidate: list[str] = field(default_factory=list)
    error: str | None = None


def run_bronze(
    name: str,
    candidate_dates: list[str],
) -> BronzeResult:
    get_settings().ensure_data_layout()
    dates_candidate = list(candidate_dates)

    try:
        result = extract_dataset(name, candidate_dates)
        if result.row_count > 0 and result.segment_keys:
            status = "success"
        else:
            status = "skipped"

        logger.info(
            "[%s] Bronze %s: candidates=%s processed=%s rows=%s path=%s",
            name,
            status,
            len(dates_candidate),
            result.segment_keys,
            result.row_count,
            result.path,
        )
        return BronzeResult(
            name=name,
            status=status,
            path=result.path,
            row_count=result.row_count,
            segment_keys=result.segment_keys,
            dates_candidate=dates_candidate,
        )
    except Exception as exc:
        logger.error("[%s] Bronze error: %s", name, exc, exc_info=True)
        return BronzeResult(
            name=name,
            status="error",
            dates_candidate=dates_candidate,
            error=str(exc),
        )


def run_bronze_phase(tasks: list[DatasetTask]) -> dict[str, BronzeResult]:
    get_settings().ensure_data_layout()
    logger.info("=== Bronze phase (%s datasets) ===", len(tasks))
    results: dict[str, BronzeResult] = {}
    for task in tasks:
        results[task.name] = run_bronze(task.name, task.dates)
    logger.info("=== Bronze phase completed ===")
    return results
