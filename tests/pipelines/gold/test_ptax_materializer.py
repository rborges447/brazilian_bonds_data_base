from __future__ import annotations

import pandas as pd
import pytest

from pipelines.gold import GoldOrchestrator, registry
from pipelines.gold.contracts import BuilderContext
from pipelines.gold.materializers.ptax import from_silver
from pipelines.silver.writer import write_partition_parquet


def test_from_silver_filters_requested_dates() -> None:
    silver = {
        "ptax": pd.DataFrame(
            {
                "data_referencia": ["2026-01-15", "2026-01-16", "2026-01-17"],
                "tipo": ["A", "A", "A"],
                "moeda": ["USD", "USD", "USD"],
                "ptax_compra": [5.10, 5.11, 5.12],
                "ptax_venda": [5.11, 5.12, 5.13],
            }
        )
    }
    ctx = BuilderContext(dates=["2026-01-15", "2026-01-17"])
    out = from_silver(silver, ctx)
    assert list(out.columns) == ["data_referencia", "ptax_compra", "ptax_venda"]
    assert list(out["data_referencia"]) == ["2026-01-15", "2026-01-17"]
    assert out.iloc[0]["ptax_compra"] == 5.10


def test_from_silver_empty_dates_returns_empty_frame() -> None:
    silver = {
        "ptax": pd.DataFrame(
            {
                "data_referencia": ["2026-01-15"],
                "ptax_compra": [5.1],
                "ptax_venda": [5.2],
            }
        )
    }
    out = from_silver(silver, BuilderContext(dates=[]))
    assert list(out.columns) == ["data_referencia", "ptax_compra", "ptax_venda"]
    assert out.empty


def test_from_silver_requires_dates() -> None:
    silver = {
        "ptax": pd.DataFrame(
            {"data_referencia": ["2026-01-15"], "ptax_compra": [5.1], "ptax_venda": [5.2]}
        )
    }
    with pytest.raises(ValueError, match="requires ctx.dates"):
        from_silver(silver, BuilderContext())


def test_from_silver_missing_date_in_silver_raises() -> None:
    silver = {
        "ptax": pd.DataFrame(
            {"data_referencia": ["2026-01-15"], "ptax_compra": [5.1], "ptax_venda": [5.2]}
        )
    }
    with pytest.raises(ValueError, match="2026-01-16"):
        from_silver(silver, BuilderContext(dates=["2026-01-15", "2026-01-16"]))


def test_from_silver_empty_silver_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        from_silver({"ptax": pd.DataFrame()}, BuilderContext(dates=["2026-01-15"]))


def test_registry_build_ptax() -> None:
    silver = {
        "ptax": pd.DataFrame(
            {
                "data_referencia": ["2026-05-01"],
                "ptax_compra": [5.5],
                "ptax_venda": [5.6],
            }
        )
    }
    out = registry.build("ptax", silver, BuilderContext(dates=["2026-05-01"]))
    assert len(out) == 1
    assert out.iloc[0]["ptax_venda"] == 5.6


def test_materialize_ptax_integration(lake_tmp_root) -> None:
    for day, compra, venda in [
        ("2026-01-15", 5.10, 5.11),
        ("2026-01-16", 5.12, 5.13),
    ]:
        write_partition_parquet(
            "ptax",
            "data",
            day,
            pd.DataFrame(
                {
                    "data_referencia": [day],
                    "tipo": ["A"],
                    "moeda": ["USD"],
                    "ptax_compra": [compra],
                    "ptax_venda": [venda],
                }
            ),
        )
    result = GoldOrchestrator().materialize_ptax(["2026-01-15", "2026-01-16"])
    assert result.name == "ptax"
    assert len(result.value) == 2
    assert list(result.value["data_referencia"]) == ["2026-01-15", "2026-01-16"]


def test_materialize_ptax_without_dates_raises() -> None:
    with pytest.raises(ValueError, match="start_date"):
        GoldOrchestrator().materialize("ptax")
