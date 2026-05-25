from __future__ import annotations

import pandas as pd
import pytest

from app.lake.gold import GoldOrchestrator
from app.lake.gold.contracts import BuilderContext
from app.lake.gold.materializers.feriados import from_silver
from app.lake.gold import registry
from app.lake.silver.writer import write_partition_parquet


def test_from_silver_returns_sorted_unique_iso_dates() -> None:
    silver = {
        "feriados": pd.DataFrame(
            {"data": ["2026-01-02", "2026-01-01", "2026-01-02"]}
        )
    }
    out = from_silver(silver, BuilderContext())
    assert out == ["2026-01-01", "2026-01-02"]


def test_from_silver_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        from_silver({"feriados": pd.DataFrame(columns=["data"])}, BuilderContext())


def test_registry_build_feriados() -> None:
    silver = {"feriados": pd.DataFrame({"data": ["2026-05-01"]})}
    out = registry.build("feriados", silver, BuilderContext())
    assert out == ["2026-05-01"]


def test_materialize_feriados_without_dates(lake_tmp_root) -> None:
    write_partition_parquet(
        "feriados",
        "snapshot",
        "1",
        pd.DataFrame({"data": ["2026-01-01", "2026-01-02"]}),
    )
    orch = GoldOrchestrator()
    result = orch.materialize("feriados")
    assert result.name == "feriados"
    assert result.value == ["2026-01-01", "2026-01-02"]
    assert "feriados" in result.silver


def test_materialize_feriados_shortcut(lake_tmp_root) -> None:
    write_partition_parquet(
        "feriados",
        "snapshot",
        "1",
        pd.DataFrame({"data": ["2026-05-01"]}),
    )
    result = GoldOrchestrator().materialize_feriados()
    assert result.value == ["2026-05-01"]


def test_read_feriados_without_dates(lake_tmp_root) -> None:
    write_partition_parquet(
        "feriados",
        "snapshot",
        "1",
        pd.DataFrame({"data": ["2026-03-15"]}),
    )
    frames = GoldOrchestrator().read_feriados()
    assert list(frames["feriados"]["data"]) == ["2026-03-15"]


def test_feriados_ignores_dates_if_passed(lake_tmp_root) -> None:
    write_partition_parquet(
        "feriados",
        "snapshot",
        "1",
        pd.DataFrame({"data": ["2026-06-01"]}),
    )
    result = GoldOrchestrator().materialize("feriados", "2099-01-01", "2099-12-31")
    assert result.value == ["2026-06-01"]
