from __future__ import annotations

import pandas as pd
import pytest

from pipelines.gold import GoldOrchestrator, registry
from pipelines.gold.contracts import BuilderContext
from pipelines.gold.materializers.liquidacoes_mercado import from_silver
from pipelines.silver.writer import write_partition_parquet

_TITULO = {
    "expressao": None,
    "data_base": "2000-01-01",
    "codigo_selic": "100000",
    "codigo_isin": "BRSTNCNTF007",
    "status": "ATIVO",
}

_LIQ_ROW = {
    "tipo_titulo": "LTN",
    "data_vencimento": "2027-01-01",
    "data_referencia": "2026-01-15",
    "qtd_operacoes": 10,
    "qtd_titulos": 1000.0,
    "pu_medio": 500.0,
    "expressao": _TITULO["expressao"],
    "data_base": _TITULO["data_base"],
    "codigo_selic": _TITULO["codigo_selic"],
    "codigo_isin": _TITULO["codigo_isin"],
}


def test_from_silver_adds_status_when_missing_in_silver() -> None:
    out = from_silver(
        {"liquidacoes_mercado": _liq_df([_LIQ_ROW])},
        BuilderContext(dates=["2026-01-15"]),
    )
    assert out.iloc[0]["status"] == "ATIVO"


def _liq_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_from_silver_filters_requested_dates() -> None:
    silver = {
        "liquidacoes_mercado": _liq_df(
            [
                _LIQ_ROW,
                {**_LIQ_ROW, "data_referencia": "2026-01-16"},
                {**_LIQ_ROW, "data_referencia": "2026-01-17"},
            ]
        )
    }
    out = from_silver(silver, BuilderContext(dates=["2026-01-15", "2026-01-17"]))
    assert len(out) == 2
    assert set(out["data_referencia"]) == {"2026-01-15", "2026-01-17"}


def test_from_silver_empty_dates_returns_empty_frame() -> None:
    silver = {"liquidacoes_mercado": _liq_df([_LIQ_ROW])}
    out = from_silver(silver, BuilderContext(dates=[]))
    assert out.empty


def test_from_silver_requires_dates() -> None:
    with pytest.raises(ValueError, match="requires ctx.dates"):
        from_silver({"liquidacoes_mercado": _liq_df([_LIQ_ROW])}, BuilderContext())


def test_from_silver_missing_date_raises() -> None:
    with pytest.raises(ValueError, match="2026-01-16"):
        from_silver(
            {"liquidacoes_mercado": _liq_df([_LIQ_ROW])},
            BuilderContext(dates=["2026-01-15", "2026-01-16"]),
        )


def test_registry_build_liquidacoes_mercado() -> None:
    out = registry.build(
        "liquidacoes_mercado",
        {"liquidacoes_mercado": _liq_df([_LIQ_ROW])},
        BuilderContext(dates=["2026-01-15"]),
    )
    assert len(out) == 1
    assert out.iloc[0]["qtd_operacoes"] == 10


def test_materialize_liquidacoes_mercado_integration(lake_tmp_root) -> None:
    for day in ("2026-01-15", "2026-01-16"):
        write_partition_parquet(
            "liquidacoes_mercado",
            "data",
            day,
            _liq_df([{**_LIQ_ROW, "data_referencia": day}]),
        )
    result = GoldOrchestrator().materialize_liquidacoes_mercado(
        ["2026-01-15", "2026-01-16"]
    )
    assert result.name == "liquidacoes_mercado"
    assert len(result.value) == 2


def test_materialize_liquidacoes_mercado_without_dates_raises() -> None:
    with pytest.raises(ValueError, match="start_date"):
        GoldOrchestrator().materialize("liquidacoes_mercado")
