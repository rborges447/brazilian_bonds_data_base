"""Silver task resolution: candidates in range where bronze exists and silver is missing."""

from __future__ import annotations

from app.core.datasets import DATASETS
from app.core.sync_range import (
    sync_business_days,
    sync_end_date,
    sync_ipca_months,
    sync_months,
    sync_start_date,
)
from app.core.partitioning import is_snapshot_dataset
from app.lake.bronze.tasks import DatasetTask
from app.lake.silver.incremental import missing_silver_partitions


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
    end = sync_end_date(target_date)
    range_start = sync_start_date(start_date)
    day_candidates = sync_business_days(end=end, start=range_start)
    month_candidates = sync_months(end=end, start=range_start)
    ipca_month_candidates = sync_ipca_months(end=end, start=range_start)

    tasks: list[DatasetTask] = []
    for cfg in DATASETS.values():
        if is_snapshot_dataset(cfg.name):
            candidates: list[str] = []
        elif cfg.name == "ipca_indice":
            candidates = ipca_month_candidates
        elif cfg.name == "projecoes":
            candidates = month_candidates
        else:
            candidates = day_candidates

        dates = missing_silver_partitions(cfg.name, candidates)
        tasks.append(DatasetTask(name=cfg.name, dates=dates, config=cfg))

    return [t for t in tasks if t.dates]
