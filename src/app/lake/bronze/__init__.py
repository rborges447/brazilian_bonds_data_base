"""Bronze pipeline: raw hive-partitioned artifacts."""

from app.contracts import BronzePartitionRef, BronzeResult, ExtractResult
from app.lake.bronze.extract_dataset import extract_dataset
from app.core.partitioning import PIPELINE_NAMES
from app.lake.bronze.reader import (
    iter_partitions_in_range,
    list_partition_values,
    partition_values_for_range,
    read_partition,
    read_partitions,
    read_range,
)
from app.lake.bronze.registry import EXTRACTORS

__all__ = [
    "EXTRACTORS",
    "BronzePartitionRef",
    "BronzeResult",
    "DatasetTask",
    "ExtractResult",
    "PIPELINE_NAMES",
    "extract_dataset",
    "iter_partitions_in_range",
    "list_partition_values",
    "partition_values_for_range",
    "read_partition",
    "read_partitions",
    "read_range",
    "resolve_bronze_tasks",
]


def __getattr__(name: str):
    if name in ("run_bronze", "run_bronze_phase"):
        from app.lake.bronze.pipeline import run_bronze, run_bronze_phase

        return {"run_bronze": run_bronze, "run_bronze_phase": run_bronze_phase}[name]
    if name in ("DatasetTask", "resolve_bronze_tasks"):
        from app.lake.bronze.tasks import DatasetTask, resolve_bronze_tasks

        return {"DatasetTask": DatasetTask, "resolve_bronze_tasks": resolve_bronze_tasks}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
