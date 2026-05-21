from __future__ import annotations

import pytest

from pipelines.gold import BUILDER_NAMES, GoldOrchestrator
from pipelines.gold.contracts import BuilderContext
from pipelines.gold import registry


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
        "vna_lft",
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
    from pipelines.gold.contracts import is_snapshot_only_builder

    assert is_snapshot_only_builder("feriados") is True
    assert is_snapshot_only_builder("cdi") is False


def test_registry_build_cdi_requires_ctx_dates() -> None:
    with pytest.raises(ValueError, match="requires ctx.dates"):
        registry.build("cdi", {}, BuilderContext())
