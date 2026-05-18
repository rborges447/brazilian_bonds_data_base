from models.datasets import (
    DATASETS,
    DatasetConfig,
    get_dataset_config,
)
from models.dates import business_days, months_in_range
from pipelines.bronze.partitioning import PIPELINE_NAMES

__all__ = [
    "DATASETS",
    "PIPELINE_NAMES",
    "DatasetConfig",
    "DatasetTask",
    "business_days",
    "get_dataset_config",
    "months_in_range",
    "resolve_bronze_tasks",
]


def __getattr__(name: str):
    if name in ("DatasetTask", "resolve_bronze_tasks"):
        from pipelines.bronze.tasks import DatasetTask, resolve_bronze_tasks

        return {
            "DatasetTask": DatasetTask,
            "resolve_bronze_tasks": resolve_bronze_tasks,
        }[name]
    raise AttributeError(f"module {name!r} has no attribute {name!r}")
