"""Incremental silver loads: bronze present and silver missing or stale."""

from __future__ import annotations

from app.core.partitioning import SNAPSHOT_VALUE, get_partition_spec, is_snapshot_dataset
from app.lake.bronze.paths import bronze_partition_path
from app.lake.silver.paths import silver_partition_path
from app.lake.silver.reader import list_partition_values
from app.lake.silver.storage import bronze_exists, partition_artifact_exists


def _bronze_newer_than_silver(dataset: str, partition_key: str, value: str) -> bool:
    bronze_path = bronze_partition_path(
        dataset, partition_key, value, get_partition_spec(dataset).artifact_ext
    )
    silver_path = silver_partition_path(dataset, partition_key, value, "parquet")
    if not bronze_path.is_file() or not silver_path.is_file():
        return False
    return bronze_path.stat().st_mtime > silver_path.stat().st_mtime


def missing_silver_partitions(dataset: str, candidate_values: list[str]) -> list[str]:
    """
    Return partition values that have bronze but no silver artifact yet.

    For ``projecoes``, also reprocess when bronze JSON is newer than silver parquet.
    For snapshot datasets, candidate_values is ignored; requires bronze snapshot=1.
    """
    spec = get_partition_spec(dataset)

    if is_snapshot_dataset(dataset):
        if not bronze_exists(
            dataset, spec.partition_key, SNAPSHOT_VALUE, spec.artifact_ext
        ):
            return []
        if partition_artifact_exists(
            dataset, spec.partition_key, SNAPSHOT_VALUE, "parquet"
        ):
            return []
        return [SNAPSHOT_VALUE]

    missing: list[str] = []
    for value in candidate_values:
        if not bronze_exists(dataset, spec.partition_key, value, spec.artifact_ext):
            continue
        if not partition_artifact_exists(dataset, spec.partition_key, value, "parquet"):
            missing.append(value)
            continue
        if dataset == "projecoes" and _bronze_newer_than_silver(
            dataset, spec.partition_key, value
        ):
            missing.append(value)
    return missing


list_existing_partition_values = list_partition_values

__all__ = [
    "missing_silver_partitions",
    "list_partition_values",
    "list_existing_partition_values",
]
