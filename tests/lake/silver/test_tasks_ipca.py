"""Silver task resolution for IPCA lookback months."""

from __future__ import annotations

import pytest

from app.lake.silver.tasks import resolve_silver_tasks


def test_resolve_silver_ipca_includes_lookback_months(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    tasks = {t.name: t for t in resolve_silver_tasks("2026-03-15")}
    if "ipca_indice" not in tasks:
        pytest.skip("all ipca silver partitions already present")
    dates = tasks["ipca_indice"].dates
    assert "2025-09-01" in dates or "2025-11-01" in dates
