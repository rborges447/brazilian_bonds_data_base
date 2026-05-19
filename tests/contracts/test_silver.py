from __future__ import annotations

from pipelines.bronze.partitioning import PIPELINE_NAMES
from pipelines.silver.registry import TRANSFORMS


def test_silver_registry_covers_all_pipelines() -> None:
    assert set(TRANSFORMS) == set(PIPELINE_NAMES)
