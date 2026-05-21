from __future__ import annotations

import pandas as pd
import pytest

from pipelines.gold import GoldOrchestrator, registry
from pipelines.gold.contracts import BuilderContext
from pipelines.gold.materializers.leiloes import from_silver
from pipelines.silver.writer import write_partition_parquet

_LEILOES_ROW = {
    "numero_edital": 100,
    "tipo_titulo": "LTN",
    "data_vencimento": "2027-01-01",
    "data_referencia": "2026-01-15",
    "oferta": 1000,
    "quantidade_aceita": 500,
    "percentual_corte": 0.5,
    "pu_medio": 500.0,
    "taxa_media": 12.5,
}


def _leiloes_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_from_silver_filters_requested_dates() -> None:
    silver = {
        "leiloes": _leiloes_df(
            [
                _LEILOES_ROW,
                {**_LEILOES_ROW, "data_referencia": "2026-01-16"},
                {**_LEILOES_ROW, "data_referencia": "2026-01-17"},
            ]
        )
    }
    out = from_silver(silver, BuilderContext(dates=["2026-01-15", "2026-01-17"]))
    assert len(out) == 2
    assert set(out["data_referencia"]) == {"2026-01-15", "2026-01-17"}


def test_from_silver_dedup_primary_key() -> None:
    silver = {
        "leiloes": _leiloes_df(
            [
                _LEILOES_ROW,
                {**_LEILOES_ROW, "oferta": 2000},
            ]
        )
    }
    out = from_silver(silver, BuilderContext(dates=["2026-01-15"]))
    assert len(out) == 1


def test_from_silver_empty_dates_returns_empty_frame() -> None:
    silver = {"leiloes": _leiloes_df([_LEILOES_ROW])}
    out = from_silver(silver, BuilderContext(dates=[]))
    assert out.empty


def test_from_silver_requires_dates() -> None:
    with pytest.raises(ValueError, match="requires ctx.dates"):
        from_silver({"leiloes": _leiloes_df([_LEILOES_ROW])}, BuilderContext())


def test_from_silver_no_partitions_returns_empty() -> None:
    out = from_silver(
        {"leiloes": pd.DataFrame()},
        BuilderContext(
            dates=["2026-01-16", "2026-01-17"],
            extras={"loaded_partitions_leiloes": []},
        ),
    )
    assert out.empty
    assert "numero_edital" in out.columns
    assert "data_referencia" in out.columns


def test_materialize_leiloes_no_partitions_returns_empty(lake_tmp_root) -> None:
    result = GoldOrchestrator().materialize_leiloes(["2099-01-01", "2099-01-02"])
    assert result.name == "leiloes"
    assert result.value.empty


def test_from_silver_skips_dates_without_silver_partition() -> None:
    """Leilões só existem em dias de leilão; partição ausente não exige linhas."""
    out = from_silver(
        {"leiloes": _leiloes_df([_LEILOES_ROW])},
        BuilderContext(
            dates=["2026-01-15", "2026-01-16"],
            extras={"loaded_partitions_leiloes": ["2026-01-15"]},
        ),
    )
    assert len(out) == 1
    assert set(out["data_referencia"]) == {"2026-01-15"}


def test_from_silver_missing_date_raises() -> None:
    with pytest.raises(ValueError, match="2026-01-16"):
        from_silver(
            {"leiloes": _leiloes_df([_LEILOES_ROW])},
            BuilderContext(dates=["2026-01-15", "2026-01-16"]),
        )


def test_registry_build_leiloes() -> None:
    out = registry.build(
        "leiloes",
        {"leiloes": _leiloes_df([_LEILOES_ROW])},
        BuilderContext(dates=["2026-01-15"]),
    )
    assert len(out) == 1
    assert out.iloc[0]["numero_edital"] == 100


def test_materialize_leiloes_integration(lake_tmp_root) -> None:
    for day in ("2026-01-15", "2026-01-16"):
        write_partition_parquet(
            "leiloes",
            "data",
            day,
            _leiloes_df([{**_LEILOES_ROW, "data_referencia": day}]),
        )
    result = GoldOrchestrator().materialize_leiloes(["2026-01-15", "2026-01-16"])
    assert result.name == "leiloes"
    assert len(result.value) == 2


def test_materialize_leiloes_without_dates_raises() -> None:
    with pytest.raises(ValueError, match="start_date"):
        GoldOrchestrator().materialize("leiloes")
