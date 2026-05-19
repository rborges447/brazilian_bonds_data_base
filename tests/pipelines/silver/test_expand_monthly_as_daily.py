from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from models.dates import business_days
from pipelines.silver.expand import read_monthly_as_daily
from pipelines.silver.writer import write_partition_parquet


def test_read_monthly_as_daily_expands_business_days(lake_tmp_root: Path) -> None:
    write_partition_parquet(
        "ipca_indice",
        "reference_month",
        "2026-01-01",
        pd.DataFrame(
            {
                "ref_month": [date(2026, 1, 1)],
                "ipca_index": [100.0],
                "ipca_mom": [0.5],
            }
        ),
    )
    write_partition_parquet(
        "ipca_indice",
        "reference_month",
        "2026-02-01",
        pd.DataFrame(
            {
                "ref_month": [date(2026, 2, 1)],
                "ipca_index": [101.0],
                "ipca_mom": [0.6],
            }
        ),
    )

    out = read_monthly_as_daily("ipca_indice", "2026-01-12", "2026-02-10")
    expected_days = business_days("2026-01-12", "2026-02-10")
    assert len(out) == len(expected_days)
    assert set(out["data_referencia"]) == set(expected_days)
    jan_rows = out[out["reference_month"] == "2026-01-01"]
    assert (jan_rows["ipca_index"] == 100.0).all()
