from __future__ import annotations

import pandas as pd

from pipelines.silver.transforms.cdi import normalize_partition


def test_cdi_normalize_renames_and_formats() -> None:
    raw = pd.DataFrame({"data": ["2026-01-15"], "valor": [13.15]})
    out = normalize_partition(raw, "2026-01-15", None)
    assert list(out.columns) == ["data_referencia", "cdi_aa"]
    assert out.iloc[0]["data_referencia"] == "2026-01-15"
    assert out.iloc[0]["cdi_aa"] == 13.15
