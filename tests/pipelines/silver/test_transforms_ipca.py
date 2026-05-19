from __future__ import annotations

import pandas as pd

from pipelines.silver.transforms.ipca_indice import normalize_partition


def test_ipca_monthly_from_sidrapy_columns() -> None:
    raw = pd.DataFrame(
        {
            "D2C": ["202601", "202601"],
            "D3C": ["2266", "63"],
            "V": [100.0, 0.5],
        }
    )
    out = normalize_partition(raw, "2026-01-01", None)
    assert len(out) == 1
    assert out.iloc[0]["ipca_index"] == 100.0
    assert out.iloc[0]["ipca_mom"] == 0.5
