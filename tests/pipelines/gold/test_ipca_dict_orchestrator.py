from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from pipelines.gold import GoldOrchestrator, registry
from pipelines.gold.contracts import BuilderContext
from pipelines.gold.materializers.ipca_dict import IPCA_DICT_COLUMNS

_IPCA = pd.DataFrame(
    [
        {"ref_month": "2026-03-01", "ipca_index": 100.0, "ipca_mom": 0.5},
        {"ref_month": "2026-04-01", "ipca_index": 101.0, "ipca_mom": 0.6},
    ]
)
_PROJ = pd.DataFrame(
    [
        {
            "indice": "IPCA",
            "tipo_projecao": "PROJEÇÕES PARA O MÊS CORRENTE",
            "ref_month": "2026-05-01",
            "data_coleta": "2026-05-05",
            "data_validade": pd.NA,
            "variacao_projetada": 0.45,
        }
    ]
)


def test_registry_build_ipca_dict_requires_feriados() -> None:
    with pytest.raises(ValueError, match="feriados"):
        registry.build(
            "ipca_dict",
            {"ipca_indice": _IPCA, "projecoes": _PROJ},
            BuilderContext(dates=["2026-05-10"]),
        )


def test_registry_build_ipca_dict_empty_dates() -> None:
    out = registry.build(
        "ipca_dict",
        {},
        BuilderContext(dates=[], extras={"feriados": set()}),
    )
    assert out.empty
    assert list(out.columns) == list(IPCA_DICT_COLUMNS)


def test_month_range_for_ipca() -> None:
    start, end = GoldOrchestrator._month_range_for_ipca(
        ["2026-05-08", "2026-05-20"]
    )
    assert start == "2026-01-01"
    assert end == "2026-05-01"


def test_materialize_ipca_dict_empty_dates() -> None:
    orch = GoldOrchestrator()
    with patch.object(orch, "resolve_feriados_set", return_value=set()):
        result = orch.materialize_ipca_dict([])
    assert result.name == "ipca_dict"
    assert result.value.empty


def test_resolve_feriados_gold_then_silver_fallback() -> None:
    orch = GoldOrchestrator()
    with patch(
        "pipelines.gold.orchestrator.read_feriados_gold",
        return_value=["2026-01-01"],
    ):
        assert orch.resolve_feriados_set() == {"2026-01-01"}

    with patch(
        "pipelines.gold.orchestrator.read_feriados_gold",
        return_value=[],
    ), patch.object(
        orch,
        "materialize_feriados",
        return_value=type("M", (), {"value": ["2026-12-25"]})(),
    ):
        assert orch.resolve_feriados_set() == {"2026-12-25"}


def test_materialize_ipca_dict_integration() -> None:
    orch = GoldOrchestrator()
    silver = {"ipca_indice": _IPCA, "projecoes": _PROJ}
    feriados: set[str] = set()
    with patch.object(orch, "read_silver", return_value=silver):
        with patch.object(orch, "resolve_feriados_set", return_value=feriados):
            result = orch.materialize_ipca_dict(["2026-05-10", "2026-05-20"])
    assert len(result.value) == 2
    row_early = result.value[result.value["data_referencia"] == "2026-05-10"].iloc[0]
    row_late = result.value[result.value["data_referencia"] == "2026-05-20"].iloc[0]
    assert row_early["usa_fechado"] == 1
    assert row_late["usa_fechado"] == 0
