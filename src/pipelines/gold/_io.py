"""Silver read helpers — sole entry point from gold to pipelines.silver.reader."""

from __future__ import annotations

from collections.abc import Iterator

import pandas as pd

from contracts import SilverPartitionRef
from pipelines.silver.reader import (
    iter_partitions_in_range,
    list_partition_values,
    partition_values_for_range,
    read_partition,
    read_partitions,
    read_range,
)

__all__ = [
    "SilverPartitionRef",
    "iter_silver_partitions_in_range",
    "list_silver_partition_values",
    "partition_values_for_range",
    "read_silver_partition",
    "read_silver_partitions",
    "read_silver_range",
]


def read_silver_range(
    dataset: str,
    start: str,
    end: str,
    *,
    skip_missing: bool = True,
    only_existing: bool = True,
    add_partition_column: bool = False,
) -> pd.DataFrame:
    return read_range(
        dataset,
        start,
        end,
        skip_missing=skip_missing,
        only_existing=only_existing,
        add_partition_column=add_partition_column,
    )


def read_silver_partition(
    dataset: str,
    partition_value: str,
    *,
    add_partition_column: bool = False,
) -> pd.DataFrame:
    return read_partition(
        dataset,
        partition_value,
        add_partition_column=add_partition_column,
    )


def read_silver_partitions(
    dataset: str,
    partition_values: list[str],
    *,
    skip_missing: bool = True,
    add_partition_column: bool = False,
) -> pd.DataFrame:
    return read_partitions(
        dataset,
        partition_values,
        skip_missing=skip_missing,
        add_partition_column=add_partition_column,
    )


def iter_silver_partitions_in_range(
    dataset: str,
    start: str,
    end: str,
    *,
    only_existing: bool = True,
) -> Iterator[SilverPartitionRef]:
    return iter_partitions_in_range(dataset, start, end, only_existing=only_existing)


def list_silver_partition_values(dataset: str) -> list[str]:
    return list_partition_values(dataset)
