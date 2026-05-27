"""Pipeline invalidation: bronze/silver partitions and gold SQLite rows."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.core.datasets import DATASETS, get_dataset_config
from app.core.partitioning import SNAPSHOT_VALUE, get_partition_spec
from app.core.dates import calendar_days
from app.core.sync_range import (
    sync_end_date,
    sync_ipca_months,
    sync_start_date,
)
from app.database.connection import get_connection
from app.lake.bronze.paths import bronze_partition_path
from app.lake.bronze.reader import partition_values_for_range
from app.lake.gold.contracts import BUILDER_SILVER_DATASETS, BuilderName
from app.lake.gold.incremental import BUILDER_TABLE, _month_first_from_day
from app.lake.silver.paths import silver_partition_path

logger = logging.getLogger(__name__)

_IPCA_DATASETS = frozenset({"ipca_indice", "projecoes"})


def _dataset_to_builder() -> dict[str, BuilderName]:
    out: dict[str, BuilderName] = {}
    for builder, silver_datasets in BUILDER_SILVER_DATASETS.items():
        for ds in silver_datasets:
            out[ds] = builder
    return out


_DATASET_TO_BUILDER = _dataset_to_builder()


def _filtered_refresh_dates(
    refresh_dates: list[str] | None,
    start: str,
    end: str,
) -> list[str] | None:
    if not refresh_dates:
        return None
    normalized = [str(d).strip()[:10] for d in refresh_dates]
    return sorted(d for d in normalized if start <= d <= end)


def _builders_for_datasets(datasets: tuple[str, ...]) -> tuple[BuilderName, ...]:
    seen: set[BuilderName] = set()
    for ds in datasets:
        builder = _DATASET_TO_BUILDER.get(ds)
        if builder is not None:
            seen.add(builder)
    return tuple(sorted(seen, key=str))


def _partition_values_for_dataset(
    dataset: str,
    start: str,
    end: str,
    refresh_dates: list[str] | None,
) -> tuple[str, ...]:
    spec = get_partition_spec(dataset)
    filtered = _filtered_refresh_dates(refresh_dates, start, end)

    if spec.granularity == "snapshot":
        return (SNAPSHOT_VALUE,)

    if spec.granularity == "month":
        if filtered:
            months = sorted({_month_first_from_day(d) for d in filtered})
            return tuple(months)
        if dataset in _IPCA_DATASETS:
            return tuple(sync_ipca_months(end=end, start=start))
        return tuple(partition_values_for_range(dataset, start, end))

    if filtered:
        return tuple(filtered)
    return tuple(partition_values_for_range(dataset, start, end))


def _gold_delete_dates_for_builder(
    builder: BuilderName,
    partition_values_by_dataset: dict[str, tuple[str, ...]],
    *,
    ipca_dict_calendar_days: tuple[str, ...],
) -> tuple[str, ...]:
    if builder == "feriados":
        return ()
    if builder == "ipca_dict":
        return ipca_dict_calendar_days

    silver_datasets = BUILDER_SILVER_DATASETS.get(builder, ())
    dates: list[str] = []
    for ds in silver_datasets:
        spec = get_partition_spec(ds)
        if spec.granularity != "day":
            continue
        dates.extend(partition_values_by_dataset.get(ds, ()))
    return tuple(sorted(set(dates)))


def _ipca_reference_months_for_scope(
    scope_datasets: tuple[str, ...],
    start: str,
    end: str,
    refresh_dates: list[str] | None,
) -> tuple[str, ...]:
    """Monthly IPCA partitions to invalidate (FR-009), aligned with refresh or sync window."""
    filtered = _filtered_refresh_dates(refresh_dates, start, end)
    if filtered:
        return tuple(sorted({_month_first_from_day(d) for d in filtered}))
    months: set[str] = set()
    for ds in scope_datasets:
        if ds in _IPCA_DATASETS:
            months.update(sync_ipca_months(end=end, start=start))
    return tuple(sorted(months))


def _ipca_dict_calendar_days_to_rebuild(
    reference_months: tuple[str, ...],
    end: str,
) -> tuple[str, ...]:
    """Calendar days in IPCA_DICT to delete/rematerialize from first impacted month through end."""
    if not reference_months:
        return ()
    first_day = min(reference_months)
    return tuple(calendar_days(first_day, end))


@dataclass(frozen=True)
class InvalidationScope:
    """Resolved destructive refresh scope for bronze, silver, and gold."""

    datasets: tuple[str, ...]
    partition_values_by_dataset: dict[str, tuple[str, ...]]
    builders: tuple[BuilderName, ...]
    gold_delete_dates_by_builder: dict[BuilderName, tuple[str, ...]]
    ipca_dict_calendar_days: tuple[str, ...]


def resolve_invalidation_scope(
    *,
    datasets: list[str] | None,
    start_date: str | None,
    end_date: str | None,
    refresh_dates: list[str] | None = None,
) -> InvalidationScope:
    """Build invalidation scope for the given datasets and date window."""
    start = sync_start_date(start_date)
    end = sync_end_date(end_date)

    if datasets is None:
        scope_datasets = tuple(sorted(DATASETS.keys()))
    else:
        scope_datasets = tuple(get_dataset_config(name).name for name in datasets)

    ipca_in_scope = any(ds in _IPCA_DATASETS for ds in scope_datasets)
    reference_months: tuple[str, ...] = ()
    if ipca_in_scope:
        reference_months = _ipca_reference_months_for_scope(
            scope_datasets, start, end, refresh_dates
        )

    partition_values_by_dataset: dict[str, tuple[str, ...]] = {}
    for ds in scope_datasets:
        if ds in _IPCA_DATASETS and reference_months:
            partition_values_by_dataset[ds] = reference_months
            continue
        values = _partition_values_for_dataset(ds, start, end, refresh_dates)
        if values:
            partition_values_by_dataset[ds] = values

    builders = _builders_for_datasets(scope_datasets)

    ipca_days = (
        _ipca_dict_calendar_days_to_rebuild(reference_months, end)
        if ipca_in_scope
        else ()
    )

    gold_delete_dates_by_builder: dict[BuilderName, tuple[str, ...]] = {}
    for builder in builders:
        gold_delete_dates_by_builder[builder] = _gold_delete_dates_for_builder(
            builder,
            partition_values_by_dataset,
            ipca_dict_calendar_days=ipca_days,
        )

    return InvalidationScope(
        datasets=scope_datasets,
        partition_values_by_dataset=partition_values_by_dataset,
        builders=builders,
        gold_delete_dates_by_builder=gold_delete_dates_by_builder,
        ipca_dict_calendar_days=ipca_days,
    )


def _assert_under_root(path: Path, root: Path) -> None:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise ValueError(
            f"Refusing to delete path outside lake root: {path} (root={root})"
        )


def _remove_partition_artifact(path: Path, lake_root: Path) -> bool:
    if not path.is_file():
        return False
    _assert_under_root(path, lake_root)
    path.unlink()
    parent = path.parent
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
    return True


def invalidate_bronze_partitions(scope: InvalidationScope) -> int:
    """Remove bronze partition artifacts in scope. Returns count of files removed."""
    settings = get_settings()
    bronze_root = settings.bronze_root
    removed = 0
    for dataset, values in scope.partition_values_by_dataset.items():
        spec = get_partition_spec(dataset)
        for value in values:
            path = bronze_partition_path(
                dataset, spec.partition_key, value, spec.artifact_ext
            )
            if _remove_partition_artifact(path, bronze_root):
                removed += 1
                logger.info("invalidated bronze partition %s", path)
    return removed


def invalidate_silver_partitions(scope: InvalidationScope) -> int:
    """Remove silver partition artifacts in scope. Returns count of files removed."""
    settings = get_settings()
    silver_root = settings.silver_root
    removed = 0
    for dataset, values in scope.partition_values_by_dataset.items():
        spec = get_partition_spec(dataset)
        for value in values:
            path = silver_partition_path(
                dataset, spec.partition_key, value, "parquet"
            )
            if _remove_partition_artifact(path, silver_root):
                removed += 1
                logger.info("invalidated silver partition %s", path)
    return removed


def invalidate_gold_persisted(
    scope: InvalidationScope,
    db_path: Path | str,
) -> int:
    """Delete gold SQLite rows in scope. Returns count of rows deleted."""
    if not Path(db_path).is_file():
        return 0

    deleted = 0
    conn = get_connection(db_path)
    try:
        for builder in scope.builders:
            meta = BUILDER_TABLE.get(builder)
            if meta is None:
                continue
            table, date_col = meta

            if builder == "feriados":
                # Snapshot: replace entire table (not per-date DELETE).
                cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = int(cur.fetchone()[0])
                if count:
                    conn.execute(f"DELETE FROM {table}")
                    deleted += count
                    logger.info(
                        "invalidated gold table %s (%d rows)", table, count
                    )
                continue

            dates = scope.gold_delete_dates_by_builder.get(builder, ())
            if not dates:
                continue

            placeholders = ",".join("?" * len(dates))
            cur = conn.execute(
                f"DELETE FROM {table} WHERE {date_col} IN ({placeholders})",
                dates,
            )
            rows = cur.rowcount
            if rows and rows > 0:
                deleted += rows
                logger.info(
                    "invalidated gold %s.%s for %d date(s) (%d rows)",
                    table,
                    date_col,
                    len(dates),
                    rows,
                )
        conn.commit()
    finally:
        conn.close()
    return deleted


@dataclass(frozen=True)
class InvalidationRunResult:
    bronze_files_removed: int
    silver_files_removed: int
    gold_rows_deleted: int


def run_pipeline_invalidation(
    *,
    datasets: list[str] | None,
    start_date: str | None,
    end_date: str | None,
    refresh_dates: list[str] | None,
    db_path: Path | str,
) -> tuple[InvalidationScope, InvalidationRunResult]:
    """Resolve scope and invalidate bronze, silver, and gold in one pass."""
    scope = resolve_invalidation_scope(
        datasets=datasets,
        start_date=start_date,
        end_date=end_date,
        refresh_dates=refresh_dates,
    )
    bronze_removed = invalidate_bronze_partitions(scope)
    silver_removed = invalidate_silver_partitions(scope)
    gold_deleted = invalidate_gold_persisted(scope, db_path)
    return scope, InvalidationRunResult(
        bronze_files_removed=bronze_removed,
        silver_files_removed=silver_removed,
        gold_rows_deleted=gold_deleted,
    )


__all__ = [
    "InvalidationRunResult",
    "InvalidationScope",
    "invalidate_bronze_partitions",
    "invalidate_gold_persisted",
    "invalidate_silver_partitions",
    "resolve_invalidation_scope",
    "run_pipeline_invalidation",
]
