from __future__ import annotations

import pandas as pd
import pytest

from app.lake.gold import GoldOrchestrator, registry
from app.lake.gold.contracts import BuilderContext
from app.lake.gold.materializers.vna import from_silver
from app.lake.silver.writer import write_partition_parquet

_REF_DATE = "2025-05-26"
_OTHER_DATE = "2025-05-27"


def _silver_row(
    date: str,
    codigo_selic: int = 210100,
    vna: float = 16616.592308,
) -> dict:
    return {
        "data_referencia": date,
        "codigo_selic": codigo_selic,
        "tipo_correcao": "O",
        "index": 14.65,
        "data_validade": "2025-05-23",
        "vna": vna,
    }


def _silver_df(rows: list[dict]) -> dict[str, pd.DataFrame]:
    return {"vna": pd.DataFrame(rows)}


def test_from_silver_filters_requested_dates() -> None:
    silver = _silver_df(
        [
            _silver_row(_REF_DATE),
            _silver_row(_OTHER_DATE, vna=16620.0),
            _silver_row("2025-05-28", vna=16625.0),
        ]
    )
    out = from_silver(silver, BuilderContext(dates=[_REF_DATE, _OTHER_DATE]))
    assert list(out.columns) == [
        "data_referencia",
        "codigo_selic",
        "tipo_correcao",
        "index",
        "data_validade",
        "vna",
        "vna_ajustado",
    ]
    assert len(out) == 2
    assert set(out["data_referencia"]) == {_REF_DATE, _OTHER_DATE}


def test_from_silver_adds_vna_ajustado_null() -> None:
    out = from_silver(_silver_df([_silver_row(_REF_DATE)]), BuilderContext(dates=[_REF_DATE]))
    assert "vna_ajustado" in out.columns
    assert out.iloc[0]["vna_ajustado"] is None or pd.isna(out.iloc[0]["vna_ajustado"])


def test_from_silver_dedup_by_natural_key() -> None:
    silver = _silver_df(
        [
            _silver_row(_REF_DATE, vna=100.0),
            _silver_row(_REF_DATE, vna=200.0),
        ]
    )
    out = from_silver(silver, BuilderContext(dates=[_REF_DATE]))
    assert len(out) == 1
    assert out.iloc[0]["vna"] == 200.0


def test_from_silver_requires_dates() -> None:
    with pytest.raises(ValueError, match="requires ctx.dates"):
        from_silver(_silver_df([_silver_row(_REF_DATE)]), BuilderContext())


def test_from_silver_missing_silver_key() -> None:
    with pytest.raises(KeyError, match="vna"):
        from_silver({}, BuilderContext(dates=[_REF_DATE]))


def test_from_silver_skips_dates_without_partition() -> None:
    out = from_silver(
        _silver_df([_silver_row(_REF_DATE)]),
        BuilderContext(
            dates=[_REF_DATE, "2026-05-01"],
            extras={"loaded_partitions_vna": [_REF_DATE]},
        ),
    )
    assert len(out) == 1
    assert list(out["data_referencia"]) == [_REF_DATE]


def test_registry_build_vna() -> None:
    out = registry.build(
        "vna",
        _silver_df([_silver_row(_REF_DATE)]),
        BuilderContext(dates=[_REF_DATE]),
    )
    assert len(out) == 1
    assert list(out.columns) == [
        "data_referencia",
        "codigo_selic",
        "tipo_correcao",
        "index",
        "data_validade",
        "vna",
        "vna_ajustado",
    ]


def test_materialize_vna_integration(lake_tmp_root) -> None:
    write_partition_parquet(
        "vna",
        "data",
        _REF_DATE,
        pd.DataFrame([_silver_row(_REF_DATE)]),
    )
    result = GoldOrchestrator().materialize_vna([_REF_DATE])
    assert result.name == "vna"
    assert len(result.value) == 1
    assert result.value.iloc[0]["codigo_selic"] == 210100
    assert "vna_ajustado" in result.value.columns
