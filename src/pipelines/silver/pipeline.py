"""Silver pipeline: bronze partition → normalize → hive silver parquet."""

from __future__ import annotations

import logging

from config import get_settings
from contracts import SilverResult
from pipelines.bronze.partitioning import get_partition_spec, is_snapshot_dataset
from pipelines.bronze.reader import read_partition as read_bronze_partition
from pipelines.silver.registry import get_transform
from pipelines.silver.tasks import DatasetTask
from pipelines.silver.writer import write_partition_parquet

logger = logging.getLogger(__name__)


def _process_partition(dataset: str, partition_value: str) -> tuple[int, str | None]:
    spec = get_partition_spec(dataset)
    transform = get_transform(dataset)
    if dataset == "projecoes":
        from pipelines.bronze.extractors._projecoes_split import load_partition_records
        from pipelines.silver.transforms.projecoes import normalize_from_records

        df_silver = normalize_from_records(load_partition_records(partition_value))
    else:
        df_bronze = read_bronze_partition(dataset, partition_value)
        df_silver = transform(df_bronze, partition_value, None)
    if df_silver is None or df_silver.empty:
        return 0, None
    write_partition_parquet(
        dataset,
        spec.partition_key,
        partition_value,
        df_silver,
    )
    return len(df_silver), partition_value


def run_silver(name: str, candidate_dates: list[str]) -> SilverResult:
    get_settings().ensure_data_layout()
    dates_candidate = list(candidate_dates)

    from pipelines.silver.incremental import missing_silver_partitions

    if is_snapshot_dataset(name):
        to_process = missing_silver_partitions(name, [])
    else:
        to_process = missing_silver_partitions(name, dates_candidate)

    if not to_process:
        logger.info("[%s] Silver skipped: no partitions to process", name)
        return SilverResult(
            name=name,
            status="skipped",
            dates_candidate=dates_candidate,
        )

    segment_keys: list[str] = []
    rows = 0
    last_path = None

    try:
        for partition_value in to_process:
            count, key = _process_partition(name, partition_value)
            if count > 0 and key:
                segment_keys.append(key)
                rows += count

        if rows > 0:
            spec = get_partition_spec(name)
            from pipelines.silver.paths import silver_partition_path

            last_path = silver_partition_path(
                name, spec.partition_key, segment_keys[-1], "parquet"
            )
            status = "success"
        else:
            status = "skipped"

        logger.info(
            "[%s] Silver %s: candidates=%s processed=%s rows=%s",
            name,
            status,
            len(dates_candidate),
            segment_keys,
            rows,
        )
        return SilverResult(
            name=name,
            status=status,
            path=last_path,
            row_count=rows,
            segment_keys=segment_keys,
            dates_candidate=dates_candidate,
        )
    except Exception as exc:
        logger.error("[%s] Silver error: %s", name, exc, exc_info=True)
        return SilverResult(
            name=name,
            status="error",
            dates_candidate=dates_candidate,
            error=str(exc),
        )


def run_silver_phase(tasks: list[DatasetTask]) -> dict[str, SilverResult]:
    get_settings().ensure_data_layout()
    logger.info("=== Silver phase (%s datasets) ===", len(tasks))
    results: dict[str, SilverResult] = {}
    for task in tasks:
        results[task.name] = run_silver(task.name, task.dates)
    logger.info("=== Silver phase completed ===")
    return results
