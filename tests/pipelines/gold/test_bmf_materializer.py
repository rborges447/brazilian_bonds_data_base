from __future__ import annotations

import pandas as pd
import pytest

from pipelines.gold import GoldOrchestrator, registry
from pipelines.gold.contracts import BuilderContext
from pipelines.gold.materializers.bmf import from_silver
from pipelines.silver.writer import write_partition_parquet

_BMF_ROW = {
    "data_referencia": "2026-01-15",
    "data_vencimento": "2027-01-01",
    "ticker": "DI1F27",
    "taxa_ajuste": 13.5,
    "quantidade_ajuste": 100.0,
    "codigo_isin": "BR0000000001",
}


def _bmf_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_from_silver_filters_requested_dates() -> None:
    silver = {
        "ajustes_bmf": _bmf_df(
            [
                _BMF_ROW,
                {**_BMF_ROW, "data_referencia": "2026-01-16", "ticker": "DAPQ26"},
                {**_BMF_ROW, "data_referencia": "2026-01-17", "ticker": "DI1G27"},
            ]
        )
    }
    ctx = BuilderContext(dates=["2026-01-15", "2026-01-17"])
    out = from_silver(silver, ctx)
    assert len(out) == 2
    assert set(out["data_referencia"]) == {"2026-01-15", "2026-01-17"}
    assert list(out.columns) == list(
        (
            "data_referencia",
            "data_vencimento",
            "ticker",
            "taxa_ajuste",
            "quantidade_ajuste",
            "codigo_isin",
        )
    )


def test_from_silver_dedup_by_date_and_ticker() -> None:
    silver = {
        "ajustes_bmf": _bmf_df([_BMF_ROW, {**_BMF_ROW, "taxa_ajuste": 99.0}])
    }
    out = from_silver(silver, BuilderContext(dates=["2026-01-15"]))
    assert len(out) == 1


def test_from_silver_empty_dates_returns_empty_frame() -> None:
    silver = {"ajustes_bmf": _bmf_df([_BMF_ROW])}
    out = from_silver(silver, BuilderContext(dates=[]))
    assert out.empty
    assert list(out.columns) == [
        "data_referencia",
        "data_vencimento",
        "ticker",
        "taxa_ajuste",
        "quantidade_ajuste",
        "codigo_isin",
    ]


def test_from_silver_requires_dates() -> None:
    silver = {"ajustes_bmf": _bmf_df([_BMF_ROW])}
    with pytest.raises(ValueError, match="requires ctx.dates"):
        from_silver(silver, BuilderContext())


def test_from_silver_missing_date_raises() -> None:
    silver = {"ajustes_bmf": _bmf_df([_BMF_ROW])}
    with pytest.raises(ValueError, match="2026-01-16"):
        from_silver(silver, BuilderContext(dates=["2026-01-15", "2026-01-16"]))


def test_from_silver_empty_silver_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        from_silver({"ajustes_bmf": pd.DataFrame()}, BuilderContext(dates=["2026-01-15"]))


def test_registry_build_bmf() -> None:
    silver = {"ajustes_bmf": _bmf_df([_BMF_ROW])}
    out = registry.build("bmf", silver, BuilderContext(dates=["2026-01-15"]))
    assert len(out) == 1
    assert out.iloc[0]["ticker"] == "DI1F27"


def test_materialize_bmf_integration(lake_tmp_root) -> None:
    for day, ticker in [("2026-01-15", "DI1F27"), ("2026-01-16", "DAPQ26")]:
        write_partition_parquet(
            "ajustes_bmf",
            "data",
            day,
            _bmf_df([{**_BMF_ROW, "data_referencia": day, "ticker": ticker}]),
        )
    result = GoldOrchestrator().materialize_bmf(["2026-01-15", "2026-01-16"])
    assert result.name == "bmf"
    assert len(result.value) == 2
    assert set(result.value["data_referencia"]) == {"2026-01-15", "2026-01-16"}


def test_materialize_bmf_without_dates_raises() -> None:
    with pytest.raises(ValueError, match="start_date"):
        GoldOrchestrator().materialize("bmf")
