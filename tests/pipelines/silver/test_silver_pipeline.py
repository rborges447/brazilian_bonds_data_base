from __future__ import annotations

from pathlib import Path
import pandas as pd

from pipelines.bronze.writer import write_partition_parquet
from pipelines.silver.pipeline import run_silver


def test_run_silver_writes_partition(lake_tmp_root: Path) -> None:
    write_partition_parquet(
        "cdi",
        "data",
        "2026-01-15",
        pd.DataFrame({"data": ["2026-01-15"], "valor": [13.0]}),
    )
    result = run_silver("cdi", ["2026-01-15"])
    assert result.status == "success"
    assert result.row_count == 1
    assert "2026-01-15" in result.segment_keys

    from pipelines.silver.reader import read_partition

    silver = read_partition("cdi", "2026-01-15")
    assert "cdi_aa" in silver.columns


def test_run_silver_skipped_when_no_bronze(lake_tmp_root: Path) -> None:
    result = run_silver("cdi", ["2099-01-01"])
    assert result.status == "skipped"
