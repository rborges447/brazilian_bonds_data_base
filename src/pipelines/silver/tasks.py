"""Silver task resolution: candidates in range where bronze exists and silver is missing."""

from __future__ import annotations

from datetime import date

from config import get_settings
from models.datasets import DATASETS
from models.dates import business_days, months_in_range
from pipelines.bronze.partitioning import is_snapshot_dataset
from pipelines.bronze.tasks import DatasetTask
from pipelines.silver.incremental import missing_silver_partitions


def resolve_silver_tasks(
    target_date: str | None = None,
    *,
    start_date: str | None = None,
) -> list[DatasetTask]:
    """
    Build silver tasks: all partition values in range with bronze present and silver missing.

    Unlike bronze ``resolve_bronze_tasks``, daily datasets use the full business-day
    candidate window, not only partitions still missing on the bronze layer.
    """
    settings = get_settings()
    if target_date is None:
        target_date = date.today().isoformat()

    range_start = start_date or settings.data_start_date.isoformat()
    day_candidates = business_days(range_start, target_date)
    month_candidates = months_in_range(range_start, target_date)

    tasks: list[DatasetTask] = []
    for cfg in DATASETS.values():
        if is_snapshot_dataset(cfg.name):
            candidates: list[str] = []
        elif cfg.name in ("projecoes", "ipca_indice"):
            candidates = month_candidates
        else:
            candidates = day_candidates

        dates = missing_silver_partitions(cfg.name, candidates)
        tasks.append(DatasetTask(name=cfg.name, dates=dates, config=cfg))

    return [t for t in tasks if t.dates]
