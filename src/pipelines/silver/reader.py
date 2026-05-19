"""
Hive-partitioned silver reader (symmetric to bronze reader).

Read normalized parquet under data/silver/{dataset}/{partition_key}={value}/part.parquet.
"""

from __future__ import annotations

from collections.abc import Iterator

import pandas as pd

from contracts import SilverPartitionRef
from models.dates import business_days, months_in_range
from pipelines.bronze.partitioning import SNAPSHOT_VALUE, get_partition_spec
from pipelines.silver.paths import silver_dataset_dir, silver_partition_path
from pipelines.silver.storage import partition_artifact_exists

__all__ = [
    "SilverPartitionRef",
    "iter_partitions_in_range",
    "list_partition_values",
    "partition_values_for_range",
    "read_partition",
    "read_partitions",
    "read_range",
]


def _partition_column_name(partition_key: str) -> str:
    return f"_partition_{partition_key}"


def list_partition_values(dataset: str) -> list[str]:
    spec = get_partition_spec(dataset)
    prefix = f"{spec.partition_key}="
    root = silver_dataset_dir(dataset)
    if not root.is_dir():
        return []
    values: list[str] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and child.name.startswith(prefix):
            val = child.name[len(prefix) :]
            if partition_artifact_exists(dataset, spec.partition_key, val, "parquet"):
                values.append(val)
    return values


def partition_values_for_range(dataset: str, start: str, end: str) -> list[str]:
    spec = get_partition_spec(dataset)
    if spec.granularity == "snapshot":
        return [SNAPSHOT_VALUE]
    if spec.granularity == "month":
        return months_in_range(start, end)
    return business_days(start, end)


def _partition_ref(dataset: str, partition_value: str) -> SilverPartitionRef:
    spec = get_partition_spec(dataset)
    path = silver_partition_path(dataset, spec.partition_key, partition_value, "parquet")
    return SilverPartitionRef(
        dataset=dataset,
        partition_key=spec.partition_key,
        partition_value=partition_value,
        path=path,
    )


def iter_partitions_in_range(
    dataset: str,
    start: str,
    end: str,
    *,
    only_existing: bool = True,
) -> Iterator[SilverPartitionRef]:
    candidates = partition_values_for_range(dataset, start, end)
    if only_existing:
        existing = set(list_partition_values(dataset))
        candidates = [v for v in candidates if v in existing]
    for value in candidates:
        yield _partition_ref(dataset, value)


def read_partition(
    dataset: str,
    partition_value: str,
    *,
    add_partition_column: bool = False,
) -> pd.DataFrame:
    ref = _partition_ref(dataset, partition_value)
    if not ref.path.is_file() or ref.path.stat().st_size == 0:
        raise FileNotFoundError(f"Silver artifact missing or empty: {ref.path}")
    df = pd.read_parquet(ref.path)
    if add_partition_column:
        col = _partition_column_name(ref.partition_key)
        df = df.copy()
        df[col] = partition_value
    return df


def read_partitions(
    dataset: str,
    partition_values: list[str],
    *,
    skip_missing: bool = True,
    add_partition_column: bool = False,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for value in partition_values:
        try:
            frames.append(
                read_partition(
                    dataset,
                    value,
                    add_partition_column=add_partition_column,
                )
            )
        except FileNotFoundError:
            if not skip_missing:
                raise
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def read_range(
    dataset: str,
    start: str,
    end: str,
    *,
    skip_missing: bool = True,
    only_existing: bool = True,
    add_partition_column: bool = False,
) -> pd.DataFrame:
    candidates = partition_values_for_range(dataset, start, end)
    if only_existing:
        existing = set(list_partition_values(dataset))
        candidates = [v for v in candidates if v in existing]
    return read_partitions(
        dataset,
        candidates,
        skip_missing=skip_missing,
        add_partition_column=add_partition_column,
    )
