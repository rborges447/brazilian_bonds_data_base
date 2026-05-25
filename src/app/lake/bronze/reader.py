"""
Hive-partitioned bronze reader (symmetric to writer.py).

Read raw artifacts under data/raw/{dataset}/{partition_key}={value}/part.{ext}
without canonical normalization. Silver pipelines should use this module instead
of opening partition paths directly.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd

from app.contracts import BronzePartitionRef
from app.core.dates import business_days, months_in_range
from app.core.partitioning import SNAPSHOT_VALUE, get_partition_spec
from app.lake.bronze.paths import bronze_dataset_dir, bronze_partition_path
from app.lake.bronze.storage import partition_artifact_exists

__all__ = [
    "BronzePartitionRef",
    "iter_partitions_in_range",
    "list_partition_values",
    "partition_values_for_range",
    "read_partition",
    "read_partitions",
    "read_range",
]


def _partition_column_name(partition_key: str) -> str:
    return f"_partition_{partition_key}"


def _load_json_artifact(path: Path) -> pd.DataFrame:
    with path.open(encoding="utf-8") as handle:
        payload: Any = json.load(handle)
    if isinstance(payload, list):
        if not payload:
            return pd.DataFrame()
        return pd.json_normalize(payload)
    return pd.DataFrame([payload])


def _load_artifact(path: Path, ext: str) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Bronze artifact missing or empty: {path}")
    if ext == "parquet":
        return pd.read_parquet(path)
    if ext == "json":
        return _load_json_artifact(path)
    raise ValueError(f"Unsupported bronze artifact extension: {ext!r}")


def list_partition_values(dataset: str) -> list[str]:
    """List partition values that have a non-empty artifact on disk."""
    spec = get_partition_spec(dataset)
    prefix = f"{spec.partition_key}="
    root = bronze_dataset_dir(dataset)
    if not root.is_dir():
        return []
    values: list[str] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and child.name.startswith(prefix):
            val = child.name[len(prefix) :]
            if partition_artifact_exists(
                dataset, spec.partition_key, val, spec.artifact_ext
            ):
                values.append(val)
    return values


def partition_values_for_range(dataset: str, start: str, end: str) -> list[str]:
    """Candidate partition values for a date range (by dataset granularity)."""
    spec = get_partition_spec(dataset)
    if spec.granularity == "snapshot":
        return [SNAPSHOT_VALUE]
    if spec.granularity == "month":
        return months_in_range(start, end)
    return business_days(start, end)


def _partition_ref(dataset: str, partition_value: str) -> BronzePartitionRef:
    spec = get_partition_spec(dataset)
    path = bronze_partition_path(
        dataset, spec.partition_key, partition_value, spec.artifact_ext
    )
    return BronzePartitionRef(
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
) -> Iterator[BronzePartitionRef]:
    """Yield partition refs in range; optionally restrict to artifacts on disk."""
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
    """Read a single hive partition artifact as a DataFrame."""
    ref = _partition_ref(dataset, partition_value)
    spec = get_partition_spec(dataset)
    df = _load_artifact(ref.path, spec.artifact_ext)
    if add_partition_column:
        col = _partition_column_name(spec.partition_key)
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
    """Read and concatenate multiple partitions (empty DataFrame if none loaded)."""
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
    """
    Read all bronze partitions in [start, end] for the dataset granularity.

    When only_existing is True (default), only partition values present on disk
    within the range are read.
    """
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
