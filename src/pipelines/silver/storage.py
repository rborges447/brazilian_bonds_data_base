"""Silver artifact presence checks."""

from __future__ import annotations

from pipelines.bronze.storage import partition_artifact_exists as bronze_partition_artifact_exists
from pipelines.silver.paths import silver_partition_path


def partition_artifact_exists(
    dataset: str,
    partition_key: str,
    value: str,
    ext: str = "parquet",
) -> bool:
    path = silver_partition_path(dataset, partition_key, value, ext)
    return path.is_file() and path.stat().st_size > 0


def bronze_exists(dataset: str, partition_key: str, value: str, ext: str) -> bool:
    return bronze_partition_artifact_exists(dataset, partition_key, value, ext)
