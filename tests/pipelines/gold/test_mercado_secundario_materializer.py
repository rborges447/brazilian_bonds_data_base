from __future__ import annotations

import pandas as pd
import pytest

from pipelines.gold import GoldOrchestrator, registry
from pipelines.gold.contracts import BuilderContext
from pipelines.gold.materializers.mercado_secundario import from_silver
from pipelines.silver.writer import write_partition_parquet

_TITULO = {
    "expressao": None,
    "data_base": "2000-01-01",
    "codigo_selic": "100000",
    "codigo_isin": "BRSTNCNTF007",
    "status": "ATIVO",
}

_MS_ROW = {
    "tipo_titulo": "LTN",
    "data_vencimento": "2027-01-01",
    "data_referencia": "2026-01-15",
    "taxa_anbima": 12.5,
    "intervalo_min_d0": 12.0,
    "intervalo_max_d0": 13.0,
    "intervalo_min_d1": 12.1,
    "intervalo_max_d1": 13.1,
    "pu": 500.0,
    "expressao": _TITULO["expressao"],
    "data_base": _TITULO["data_base"],
    "codigo_selic": _TITULO["codigo_selic"],
    "codigo_isin": _TITULO["codigo_isin"],
}


def test_from_silver_adds_status_when_missing_in_silver() -> None:
    out = from_silver(
        {"mercado_secundario": _ms_df([_MS_ROW])},
        BuilderContext(dates=["2026-01-15"]),
    )
    assert "status" in out.columns
    assert out.iloc[0]["status"] == "ATIVO"


def _ms_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_from_silver_filters_requested_dates() -> None:
    silver = {
        "mercado_secundario": _ms_df(
            [
                _MS_ROW,
                {**_MS_ROW, "data_referencia": "2026-01-16", "tipo_titulo": "NTN-B"},
                {**_MS_ROW, "data_referencia": "2026-01-17"},
            ]
        )
    }
    out = from_silver(silver, BuilderContext(dates=["2026-01-15", "2026-01-17"]))
    assert len(out) == 2
    assert set(out["data_referencia"]) == {"2026-01-15", "2026-01-17"}


def test_from_silver_dedup_by_date_titulo_vencimento() -> None:
    silver = {"mercado_secundario": _ms_df([_MS_ROW, {**_MS_ROW, "taxa_anbima": 99.0}])}
    out = from_silver(silver, BuilderContext(dates=["2026-01-15"]))
    assert len(out) == 1


def test_from_silver_empty_dates_returns_empty_frame() -> None:
    silver = {"mercado_secundario": _ms_df([_MS_ROW])}
    out = from_silver(silver, BuilderContext(dates=[]))
    assert out.empty


def test_from_silver_requires_dates() -> None:
    with pytest.raises(ValueError, match="requires ctx.dates"):
        from_silver({"mercado_secundario": _ms_df([_MS_ROW])}, BuilderContext())


def test_from_silver_missing_date_raises() -> None:
    with pytest.raises(ValueError, match="2026-01-16"):
        from_silver(
            {"mercado_secundario": _ms_df([_MS_ROW])},
            BuilderContext(dates=["2026-01-15", "2026-01-16"]),
        )


def test_registry_build_mercado_secundario() -> None:
    out = registry.build(
        "mercado_secundario",
        {"mercado_secundario": _ms_df([_MS_ROW])},
        BuilderContext(dates=["2026-01-15"]),
    )
    assert len(out) == 1
    assert out.iloc[0]["tipo_titulo"] == "LTN"


def test_materialize_mercado_secundario_integration(lake_tmp_root) -> None:
    for day in ("2026-01-15", "2026-01-16"):
        write_partition_parquet(
            "mercado_secundario",
            "data",
            day,
            _ms_df([{**_MS_ROW, "data_referencia": day}]),
        )
    result = GoldOrchestrator().materialize_mercado_secundario(
        ["2026-01-15", "2026-01-16"]
    )
    assert result.name == "mercado_secundario"
    assert len(result.value) == 2


def test_materialize_mercado_secundario_without_dates_raises() -> None:
    with pytest.raises(ValueError, match="start_date"):
        GoldOrchestrator().materialize("mercado_secundario")
