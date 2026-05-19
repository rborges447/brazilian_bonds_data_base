from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from pipelines.bronze.writer import write_partition_json
from pipelines.silver.incremental import missing_silver_partitions
from pipelines.silver.writer import write_partition_parquet


def test_missing_silver_projecoes_when_bronze_newer(lake_tmp_root: Path) -> None:
    write_partition_json(
        "projecoes",
        "reference_month",
        "2026-05-01",
        [{"indice": "IPCA", "mes_referencia": "05/2026", "data_coleta": "2026-05-12"}],
    )
    write_partition_parquet(
        "projecoes",
        "reference_month",
        "2026-05-01",
        pd.DataFrame({"indice": ["IPCA"]}),
    )

    time.sleep(0.05)
    write_partition_json(
        "projecoes",
        "reference_month",
        "2026-05-01",
        [
            {"indice": "IPCA", "mes_referencia": "05/2026", "data_coleta": "2026-05-12"},
            {"indice": "IPCA", "mes_referencia": "05/2026", "data_coleta": "2026-05-19"},
        ],
    )

    missing = missing_silver_partitions("projecoes", ["2026-05-01"])
    assert "2026-05-01" in missing
