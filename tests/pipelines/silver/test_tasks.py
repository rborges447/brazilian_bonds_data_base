from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pipelines.bronze.writer import write_partition_parquet
from pipelines.bronze.tasks import resolve_bronze_tasks
from pipelines.silver.tasks import resolve_silver_tasks


def test_resolve_silver_tasks_includes_bronze_complete_partitions(
    lake_tmp_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Silver must process bronze-complete partitions, not only bronze-missing ones."""
    monkeypatch.setenv("DATA_START_DATE", "2026-01-15")
    get_settings = __import__("config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    write_partition_parquet(
        "cdi",
        "data",
        "2026-01-15",
        pd.DataFrame({"data": ["2026-01-15"], "valor": [13.0]}),
    )

    bronze_tasks = resolve_bronze_tasks("2026-01-15")
    bronze_cdi = next(t for t in bronze_tasks if t.name == "cdi")
    assert "2026-01-15" not in bronze_cdi.dates

    silver_tasks = resolve_silver_tasks("2026-01-15")
    silver_cdi = next(t for t in silver_tasks if t.name == "cdi")
    assert "2026-01-15" in silver_cdi.dates
