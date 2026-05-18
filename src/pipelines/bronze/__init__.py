"""Bronze pipeline: raw hive-partitioned artifacts."""

from contracts import ExtractResult
from pipelines.bronze.extract_dataset import extract_dataset
from pipelines.bronze.reader import (
    BronzePartitionRef,
    iter_partitions_in_range,
    list_partition_values,
    partition_values_for_range,
    read_partition,
    read_partitions,
    read_range,
)
from pipelines.bronze.registry import EXTRACTORS

__all__ = [
    "EXTRACTORS",
    "BronzePartitionRef",
    "ExtractResult",
    "extract_dataset",
    "iter_partitions_in_range",
    "list_partition_values",
    "partition_values_for_range",
    "read_partition",
    "read_partitions",
    "read_range",
]


def __getattr__(name: str):
    if name in ("BronzeResult", "run_bronze", "run_bronze_phase"):
        from pipelines.bronze.pipeline import BronzeResult, run_bronze, run_bronze_phase

        return {"BronzeResult": BronzeResult, "run_bronze": run_bronze, "run_bronze_phase": run_bronze_phase}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
