from __future__ import annotations

import pandas as pd

from app.lake.silver.transforms.cdi import normalize_partition


def test_cdi_normalize_renames_and_formats() -> None:
    raw = pd.DataFrame(
        {
            "data_referencia": ["2026-01-15"],
            "estimativa_taxa_selic": [14.75],
        }
    )
    out = normalize_partition(raw, "2026-01-15", None)
    assert list(out.columns) == ["data_referencia", "cdi"]
    assert out.iloc[0]["data_referencia"] == "2026-01-15"
    assert out.iloc[0]["cdi"] == 14.75
