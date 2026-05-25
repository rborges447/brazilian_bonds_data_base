"""Shared domain utilities: dates, dataset registry, partition specs."""

from app.core.dates import business_days, iso_month_first, months_in_range
from app.core.datasets import DATASETS, DatasetConfig, DateMode, get_dataset_config
from app.core.partitioning import (
    PARTITION_SPECS,
    PIPELINE_NAMES,
    SNAPSHOT_VALUE,
    DatasetPartitionSpec,
    Granularity,
    get_partition_spec,
    is_snapshot_dataset,
)
from app.core.exceptions import (
    DatasetNotFoundError,
    PartitionMissingError,
    PipelineError,
)

__all__ = [
    "DATASETS",
    "DatasetConfig",
    "DatasetNotFoundError",
    "DatasetPartitionSpec",
    "DateMode",
    "Granularity",
    "PARTITION_SPECS",
    "PartitionMissingError",
    "PipelineError",
    "PIPELINE_NAMES",
    "SNAPSHOT_VALUE",
    "business_days",
    "get_dataset_config",
    "get_partition_spec",
    "iso_month_first",
    "is_snapshot_dataset",
    "months_in_range",
]
