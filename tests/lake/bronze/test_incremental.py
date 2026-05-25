from __future__ import annotations

from app.lake.bronze.incremental import list_existing_partition_values, missing_partition_values
from app.core.partitioning import SNAPSHOT_VALUE
import pandas as pd

from app.lake.bronze.writer import write_partition_json, write_partition_parquet


def test_missing_partition_values_daily(bronze_tmp_root) -> None:
    write_partition_json("mercado_secundario", "data", "2026-01-10", [])
    missing = missing_partition_values(
        "mercado_secundario",
        ["2026-01-10", "2026-01-11"],
    )
    assert missing == ["2026-01-11"]


def test_missing_snapshot_skips_when_present(bronze_tmp_root) -> None:
    write_partition_parquet(
        "feriados",
        "snapshot",
        SNAPSHOT_VALUE,
        pd.DataFrame({"Data": ["2026-01-01"]}),
    )
    missing = missing_partition_values("feriados", [])
    assert missing == []


def test_list_existing_partition_values(bronze_tmp_root) -> None:
    write_partition_json("mercado_secundario", "data", "2026-01-12", {"a": 1})
    values = list_existing_partition_values("mercado_secundario")
    assert values == ["2026-01-12"]
