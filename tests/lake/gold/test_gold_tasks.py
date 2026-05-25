from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.lake.bronze.writer import write_partition_parquet
from app.lake.gold.tasks import resolve_gold_tasks
from app.lake.silver.writer import write_partition_parquet as write_silver_partition


def test_resolve_gold_tasks_only_dates_with_silver(
    lake_tmp_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-15")
    from app.config import get_settings

    get_settings.cache_clear()

    write_partition_parquet(
        "cdi",
        "data",
        "2026-01-15",
        pd.DataFrame({"data": ["2026-01-15"], "valor": [13.0]}),
    )
    write_silver_partition(
        "cdi",
        "data",
        "2026-01-15",
        pd.DataFrame({"data_referencia": ["2026-01-15"], "cdi": [13.0]}),
    )

    tasks = resolve_gold_tasks("2026-01-15", persist=False)
    cdi_task = next(t for t in tasks if t.name == "cdi")
    assert "2026-01-15" in cdi_task.dates
    assert "2026-01-16" not in cdi_task.dates
