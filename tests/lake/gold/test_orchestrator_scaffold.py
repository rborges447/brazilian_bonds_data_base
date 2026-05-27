from __future__ import annotations

import pytest

from app.lake.gold import BUILDER_NAMES, GoldOrchestrator
from app.lake.gold.contracts import BuilderContext
from app.lake.gold import registry


def test_builder_names() -> None:
    assert set(BUILDER_NAMES) == {
        "feriados",
        "cdi",
        "ptax",
        "bmf",
        "mercado_secundario",
        "liquidacoes_mercado",
        "leiloes",
        "ipca_dict",
        "vna",
    }


def test_read_silver_unknown_builder() -> None:
    orch = GoldOrchestrator()
    with pytest.raises(ValueError, match="Unknown builder"):
        orch.read_silver("invalid", "2026-01-01", "2026-01-31")  # type: ignore[arg-type]


def test_materialize_cdi_without_dates_or_ctx_raises() -> None:
    orch = GoldOrchestrator()
    with pytest.raises(ValueError, match="start_date"):
        orch.materialize("cdi")


def test_is_snapshot_only_feriados() -> None:
    from app.lake.gold.contracts import is_snapshot_only_builder

    assert is_snapshot_only_builder("feriados") is True
    assert is_snapshot_only_builder("cdi") is False


def test_registry_build_cdi_requires_ctx_dates() -> None:
    with pytest.raises(ValueError, match="requires ctx.dates"):
        registry.build("cdi", {}, BuilderContext())


def test_registry_build_ipca_dict_requires_feriados_key_in_extras() -> None:
    with pytest.raises(ValueError, match="feriados"):
        registry.build("ipca_dict", {}, BuilderContext(dates=["2026-05-15"]))
