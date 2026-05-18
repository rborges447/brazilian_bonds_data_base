"""Write raw bronze artifacts into hive partitions (no schema normalization)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from pipelines.bronze.partitioning import DatasetPartitionSpec, get_partition_spec
from pipelines.bronze.paths import bronze_partition_path
from pipelines.bronze.storage import partition_artifact_exists

__all__ = [
    "partition_artifact_exists",
    "write_dataframe_partitions",
    "write_partition_json",
    "write_partition_parquet",
    "write_raw_json",
    "write_raw_parquet",
]


def ensure_partition_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_raw_json(path: Path, payload: Any) -> Path:
    ensure_partition_dir(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, default=str)
    return path


def write_raw_parquet(path: Path, df: pd.DataFrame) -> Path:
    ensure_partition_dir(path)
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    return path


def write_partition_json(
    dataset: str,
    partition_key: str,
    value: str,
    payload: Any,
    ext: str = "json",
) -> Path:
    path = bronze_partition_path(dataset, partition_key, value, ext)
    return write_raw_json(path, payload)


def write_partition_parquet(
    dataset: str,
    partition_key: str,
    value: str,
    df: pd.DataFrame,
    ext: str = "parquet",
) -> Path:
    path = bronze_partition_path(dataset, partition_key, value, ext)
    return write_raw_parquet(path, df)


def write_dataframe_partitions(
    df: pd.DataFrame,
    spec: DatasetPartitionSpec,
    date_col: str,
    only_values: set[str] | None = None,
) -> tuple[list[str], int, Path | None]:
    """Split a raw DataFrame by date column and write one parquet per partition."""
    from pipelines.bronze._split import split_dataframe_by_partition

    if df.empty:
        return [], 0, None

    parts = split_dataframe_by_partition(df, date_col, spec.granularity)
    keys: list[str] = []
    rows = 0
    last_path: Path | None = None
    for part_val, chunk in parts.items():
        if only_values is not None and part_val not in only_values:
            continue
        last_path = write_partition_parquet(
            spec.dataset,
            spec.partition_key,
            part_val,
            chunk,
            spec.artifact_ext,
        )
        keys.append(part_val)
        rows += len(chunk)
    return keys, rows, last_path
