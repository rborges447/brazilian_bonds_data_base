from __future__ import annotations

from app.core.partitioning import PIPELINE_NAMES
from app.lake.silver.registry import TRANSFORMS

def test_silver_registry_covers_all_pipelines() -> None:
    assert set(TRANSFORMS) == set(PIPELINE_NAMES)
