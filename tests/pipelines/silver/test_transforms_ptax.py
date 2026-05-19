from __future__ import annotations

import pandas as pd

from pipelines.silver.transforms.ptax import normalize_partition


def test_ptax_drops_paridade_and_filters_tipo_a() -> None:
    raw = pd.DataFrame(
        {
            "data": ["2026-01-15", "2026-01-15"],
            "codigo": [61, 61],
            "tipo": ["A", "I"],
            "moeda": ["USD", "USD"],
            "taxa_compra": [5.1, 5.2],
            "taxa_venda": [5.2, 5.3],
            "paridade_compra": [1.0, 1.0],
            "paridade_venda": [1.0, 1.0],
        }
    )
    out = normalize_partition(raw, "2026-01-15", None)
    assert len(out) == 1
    assert "paridade_compra" not in out.columns
    assert "codigo" not in out.columns
    assert out.iloc[0]["ptax_compra"] == 5.1
