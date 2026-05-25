"""Gold incremental: ipca_dict uses calendar days with IPCA lookback silver."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.lake.gold.incremental import _dates_ipca_dict_buildable, _dates_silver_ready


def test_ipca_dict_buildable_in_may_without_current_month_ipca(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """May days are buildable when proj exists and IPCA through April is in silver."""
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()

    def fake_silver(ds: str, vals: list[str]) -> list[str]:
        if ds == "ipca_indice":
            return [m for m in vals if m <= "2026-04-01"]
        if ds == "projecoes":
            return [m for m in vals if m in ("2026-05-01",)]
        return vals

    with patch(
        "app.lake.gold.incremental._values_with_silver",
        side_effect=fake_silver,
    ):
        buildable = _dates_ipca_dict_buildable(["2026-05-15"])

    assert buildable == ["2026-05-15"]


def test_ipca_dict_requires_ipca_lookback_months_in_silver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only calendar month with proj but without IPCA lookback is not buildable."""
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    candidates = ["2026-01-15"]

    def fake_silver(ds: str, vals: list[str]) -> list[str]:
        if ds == "ipca_indice":
            return ["2026-01-01"]
        return vals

    with patch(
        "app.lake.gold.incremental._values_with_silver",
        side_effect=fake_silver,
    ):
        assert _dates_ipca_dict_buildable(candidates) == []


def test_ipca_dict_candidates_all_days_when_month_partitions_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    candidates = ["2026-02-01", "2026-02-02", "2026-02-03"]
    with patch(
        "app.lake.gold.incremental._values_with_silver",
        side_effect=lambda ds, vals: vals,
    ):
        buildable = _dates_ipca_dict_buildable(candidates)
        ready = _dates_silver_ready("ipca_dict", candidates)

    assert buildable == candidates
    assert ready == candidates
