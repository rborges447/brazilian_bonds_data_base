from __future__ import annotations

import pandas as pd

from app.core.partitioning import get_partition_spec
from app.lake.bronze.paths import bronze_partition_path
from app.lake.bronze.writer import (
    partition_artifact_exists,
    write_dataframe_partitions,
    write_partition_json,
)


def test_write_partition_json(bronze_tmp_root) -> None:
    path = write_partition_json("mercado_secundario", "data", "2026-01-20", [{"x": 1}])
    assert path.is_file()
    assert partition_artifact_exists("mercado_secundario", "data", "2026-01-20", "json")


def test_write_dataframe_partitions_preserves_columns(bronze_tmp_root) -> None:
    df = pd.DataFrame(
        {
            "DATA MOV": ["15/01/2026", "16/01/2026"],
            "TICKER": ["A", "B"],
        }
    )
    spec = get_partition_spec("liquidacoes_mercado")
    keys, rows, _ = write_dataframe_partitions(
        df,
        spec,
        "DATA MOV",
        only_values={"2026-01-15", "2026-01-16"},
    )
    assert rows == 2
    assert set(keys) == {"2026-01-15", "2026-01-16"}
    part = bronze_partition_path("liquidacoes_mercado", "data", "2026-01-15", "parquet")
    loaded = pd.read_parquet(part)
    assert list(loaded.columns) == ["DATA MOV", "TICKER"]
