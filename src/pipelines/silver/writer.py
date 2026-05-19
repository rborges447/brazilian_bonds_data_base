"""Write normalized silver artifacts into hive partitions."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipelines.bronze.partitioning import get_partition_spec
from pipelines.silver.paths import silver_partition_path


def ensure_partition_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_raw_parquet(path: Path, df: pd.DataFrame) -> Path:
    ensure_partition_dir(path)
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    return path


def write_partition_parquet(
    dataset: str,
    partition_key: str,
    value: str,
    df: pd.DataFrame,
    ext: str = "parquet",
) -> Path:
    path = silver_partition_path(dataset, partition_key, value, ext)
    return write_raw_parquet(path, df)
