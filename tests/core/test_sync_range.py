from __future__ import annotations

import pytest

from app.core.sync_range import (
    sync_business_days,
    sync_calendar_days,
    sync_end_date,
    sync_ipca_month_start,
    sync_ipca_months,
    sync_months,
    sync_start_date,
)


def test_sync_start_date_clamps_before_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-15")
    from app.config import get_settings

    get_settings.cache_clear()
    assert sync_start_date("2020-01-01") == "2026-01-15"
    assert sync_start_date() == "2026-01-15"


def test_sync_end_date_default_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    assert sync_end_date("2026-02-01") == "2026-02-01"


def test_sync_business_days_respects_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-15")
    from app.config import get_settings

    get_settings.cache_clear()
    days = sync_business_days(end="2026-01-20", start="2026-01-01")
    assert days[0] >= "2026-01-15"
    assert days[-1] <= "2026-01-20"


def test_sync_months(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    months = sync_months(end="2026-03-15", start="2026-01-01")
    assert months == ["2026-01-01", "2026-02-01", "2026-03-01"]


def test_sync_calendar_days_includes_weekends(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    days = sync_calendar_days(end="2026-01-07", start="2026-01-01")
    assert days == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
        "2026-01-05",
        "2026-01-06",
        "2026-01-07",
    ]


def test_sync_ipca_months_includes_lookback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    assert sync_ipca_month_start() == "2025-09-01"
    months = sync_ipca_months(end="2026-02-01", start="2026-01-01")
    assert months[0] == "2025-09-01"
    assert "2026-01-01" in months
    assert months[-1] == "2026-02-01"
