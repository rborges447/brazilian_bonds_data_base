"""Bronze task resolution (partition-aware date lists per dataset)."""

from __future__ import annotations

from dataclasses import dataclass, field
from app.core.datasets import DATASETS, DatasetConfig
from app.core.sync_range import (
    sync_business_days,
    sync_end_date,
    sync_ipca_months,
    sync_months,
    sync_start_date,
)
from app.lake.bronze.incremental import missing_partition_values
from app.core.partitioning import is_snapshot_dataset


@dataclass
class DatasetTask:
    name: str
    dates: list[str] = field(default_factory=list)
    config: DatasetConfig | None = None


def _dates_for_dataset(
    cfg: DatasetConfig,
    end_date: str,
    day_candidates: list[str],
    month_candidates: list[str],
    ipca_month_candidates: list[str],
    range_start: str,
) -> list[str]:
    if cfg.date_mode == "missing_dates":
        return missing_partition_values(cfg.name, day_candidates)
    if cfg.name == "ipca_indice":
        return ipca_month_candidates
    if cfg.name == "projecoes":
        return month_candidates
    if is_snapshot_dataset(cfg.name):
        return []
    return []


def resolve_bronze_tasks(
    target_date: str | None = None,
    *,
    start_date: str | None = None,
) -> list[DatasetTask]:
    """
    Build bronze tasks with partition-aware candidate dates.

    By default uses business days from DATA_START_DATE through target_date.
    When start_date is set (backfill), candidates are business_days(start_date, target_date).
    """
    end = sync_end_date(target_date)
    range_start = sync_start_date(start_date)
    day_candidates = sync_business_days(end=end, start=range_start)
    month_candidates = sync_months(end=end, start=range_start)
    ipca_month_candidates = sync_ipca_months(end=end, start=range_start)

    tasks: list[DatasetTask] = []
    for cfg in DATASETS.values():
        dates = _dates_for_dataset(
            cfg,
            end,
            day_candidates,
            month_candidates,
            ipca_month_candidates,
            range_start,
        )
        tasks.append(DatasetTask(name=cfg.name, dates=dates, config=cfg))
    return tasks
