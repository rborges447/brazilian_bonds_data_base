from __future__ import annotations

from pathlib import Path
import pandas as pd

from app.lake.bronze.writer import write_partition_parquet
from app.lake.silver.pipeline import run_silver


def test_run_silver_writes_partition(lake_tmp_root: Path) -> None:
    write_partition_parquet(
        "cdi",
        "data",
        "2026-01-15",
        pd.DataFrame(
            {
                "data_referencia": ["2026-01-15"],
                "estimativa_taxa_selic": [14.75],
            }
        ),
    )
    result = run_silver("cdi", ["2026-01-15"])
    assert result.status == "success"
    assert result.row_count == 1
    assert "2026-01-15" in result.segment_keys

    from app.lake.silver.reader import read_partition

    silver = read_partition("cdi", "2026-01-15")
    assert "cdi" in silver.columns
    assert silver.iloc[0]["cdi"] == 14.75


def test_run_silver_skipped_when_no_bronze(lake_tmp_root: Path) -> None:
    result = run_silver("cdi", ["2099-01-01"])
    assert result.status == "skipped"
