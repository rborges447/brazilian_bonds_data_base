"""Bronze task resolution (partition-aware date lists per dataset)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from config import get_settings
from models.datasets import DATASETS, DatasetConfig
from models.dates import business_days, months_in_range
from pipelines.bronze.incremental import missing_partition_values
from pipelines.bronze.partitioning import is_snapshot_dataset


@dataclass
class DatasetTask:
    name: str
    dates: list[str] = field(default_factory=list)
    config: DatasetConfig | None = None


def _dates_for_dataset(
    cfg: DatasetConfig,
    target_date: str,
    candidates: list[str],
    range_start: str,
) -> list[str]:
    if cfg.date_mode == "missing_dates":
        return missing_partition_values(cfg.name, candidates)
    if cfg.name in ("projecoes", "ipca_indice"):
        return months_in_range(range_start, target_date)
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
    settings = get_settings()
    if target_date is None:
        target_date = date.today().isoformat()

    range_start = start_date or settings.data_start_date.isoformat()
    candidates = business_days(range_start, target_date)

    tasks: list[DatasetTask] = []
    for cfg in DATASETS.values():
        dates = _dates_for_dataset(cfg, target_date, candidates, range_start)
        tasks.append(DatasetTask(name=cfg.name, dates=dates, config=cfg))
    return tasks
