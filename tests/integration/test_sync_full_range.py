"""Short-range sync coverage (bronze gaps → silver gaps chain)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.core.sync_verify import bronze_gaps, silver_gaps, sync_status_report
from app.lake.bronze.writer import write_partition_parquet


def test_bronze_then_silver_gap_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DATA_START_DATE", "2026-01-15")
    from app.config import get_settings

    get_settings.cache_clear()
    get_settings().ensure_data_layout()

    end = "2026-01-15"
    assert "2026-01-15" in bronze_gaps("cdi", end, end)

    write_partition_parquet(
        "cdi",
        "data",
        end,
        pd.DataFrame({"data": [end], "valor": [13.0]}),
    )
    assert "2026-01-15" not in bronze_gaps("cdi", end, end)
    assert "2026-01-15" in silver_gaps("cdi", end, end)

    report = sync_status_report(end, check_persist=False)
    assert "cdi" in report["silver"]
