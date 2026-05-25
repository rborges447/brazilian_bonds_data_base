from __future__ import annotations

import pandas as pd
import pytest

from app.lake.gold import GoldOrchestrator, registry
from app.lake.gold.contracts import BuilderContext
from app.lake.gold.materializers.cdi import from_silver
from app.lake.silver.writer import write_partition_parquet


def test_from_silver_filters_requested_dates() -> None:
    silver = {
        "cdi": pd.DataFrame(
            {
                "data_referencia": ["2026-01-15", "2026-01-16", "2026-01-17"],
                "cdi": [14.75, 14.80, 14.85],
            }
        )
    }
    ctx = BuilderContext(dates=["2026-01-15", "2026-01-17"])
    out = from_silver(silver, ctx)
    assert list(out.columns) == ["data_referencia", "cdi"]
    assert list(out["data_referencia"]) == ["2026-01-15", "2026-01-17"]
    assert out.iloc[0]["cdi"] == 14.75


def test_from_silver_empty_dates_returns_empty_frame() -> None:
    silver = {
        "cdi": pd.DataFrame(
            {"data_referencia": ["2026-01-15"], "cdi": [14.75]}
        )
    }
    out = from_silver(silver, BuilderContext(dates=[]))
    assert list(out.columns) == ["data_referencia", "cdi"]
    assert out.empty


def test_from_silver_requires_dates() -> None:
    silver = {"cdi": pd.DataFrame({"data_referencia": ["2026-01-15"], "cdi": [1.0]})}
    with pytest.raises(ValueError, match="requires ctx.dates"):
        from_silver(silver, BuilderContext())


def test_from_silver_missing_date_in_silver_raises() -> None:
    silver = {
        "cdi": pd.DataFrame(
            {"data_referencia": ["2026-01-15"], "cdi": [14.75]}
        )
    }
    with pytest.raises(ValueError, match="2026-01-16"):
        from_silver(silver, BuilderContext(dates=["2026-01-15", "2026-01-16"]))


def test_from_silver_empty_silver_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        from_silver(
            {"cdi": pd.DataFrame()},
            BuilderContext(
                dates=["2026-01-15"],
                extras={"loaded_partitions_cdi": ["2026-01-15"]},
            ),
        )


def test_from_silver_skips_dates_without_silver_partition() -> None:
    """Backfill: dias sem partição silver (feriado / ingestão parcial) não bloqueiam gold."""
    out = from_silver(
        {
            "cdi": pd.DataFrame(
                {"data_referencia": ["2026-01-15"], "cdi": [14.75]}
            )
        },
        BuilderContext(
            dates=["2026-01-15", "2026-05-01"],
            extras={"loaded_partitions_cdi": ["2026-01-15"]},
        ),
    )
    assert len(out) == 1
    assert list(out["data_referencia"]) == ["2026-01-15"]


def test_registry_build_cdi() -> None:
    silver = {
        "cdi": pd.DataFrame(
            {"data_referencia": ["2026-05-01"], "cdi": [14.9]}
        )
    }
    out = registry.build("cdi", silver, BuilderContext(dates=["2026-05-01"]))
    assert len(out) == 1
    assert out.iloc[0]["cdi"] == 14.9


def test_materialize_cdi_integration(lake_tmp_root) -> None:
    for day, rate in [("2026-01-15", 14.75), ("2026-01-16", 14.80)]:
        write_partition_parquet(
            "cdi",
            "data",
            day,
            pd.DataFrame({"data_referencia": [day], "cdi": [rate]}),
        )
    result = GoldOrchestrator().materialize_cdi(["2026-01-15", "2026-01-16"])
    assert result.name == "cdi"
    assert len(result.value) == 2
    assert list(result.value["data_referencia"]) == ["2026-01-15", "2026-01-16"]


def test_materialize_cdi_without_dates_raises() -> None:
    with pytest.raises(ValueError, match="start_date"):
        GoldOrchestrator().materialize("cdi")
