"""Canonical sync interval anchored at DATA_START_DATE (.env)."""

from __future__ import annotations

from datetime import date

import pandas as pd

from app.config import get_settings
from app.core.dates import business_days, calendar_days, months_in_range

IPCA_MONTH_LOOKBACK = 4


def sync_end_date(override: str | None = None) -> str:
    """Inclusive end of sync window (default: today)."""
    if override is not None:
        return str(override).strip()[:10]
    return date.today().isoformat()


def sync_start_date(override: str | None = None) -> str:
    """Inclusive start of sync window (never before DATA_START_DATE)."""
    floor = get_settings().data_start_date
    if override is None:
        return floor.isoformat()
    requested = date.fromisoformat(str(override).strip()[:10])
    start = max(requested, floor)
    return start.isoformat()


def sync_business_days(
    end: str | None = None,
    start: str | None = None,
) -> list[str]:
    """Business days in [sync_start_date, sync_end_date]."""
    return business_days(sync_start_date(start), sync_end_date(end))


def sync_months(end: str | None = None, start: str | None = None) -> list[str]:
    """Calendar months (YYYY-MM-01) in the sync window."""
    return months_in_range(sync_start_date(start), sync_end_date(end))


def sync_calendar_days(end: str | None = None, start: str | None = None) -> list[str]:
    """Every calendar day in [sync_start_date, sync_end_date] (incl. weekends/holidays)."""
    return calendar_days(sync_start_date(start), sync_end_date(end))


def sync_ipca_month_start() -> str:
    """First month (YYYY-MM-01) loaded for IPCA lookback before DATA_START_DATE."""
    floor = pd.Timestamp(get_settings().data_start_date.isoformat()).normalize()
    start = floor - pd.DateOffset(months=IPCA_MONTH_LOOKBACK)
    return start.strftime("%Y-%m-01")


def sync_ipca_months(end: str | None = None, start: str | None = None) -> list[str]:
    """Calendar months for IPCA bronze/silver (lookback + product window)."""
    range_end = sync_end_date(end)
    range_start = sync_start_date(start)
    ipca_start = sync_ipca_month_start()
    start_month = min(range_start, ipca_start)
    return months_in_range(start_month, range_end)


__all__ = [
    "IPCA_MONTH_LOOKBACK",
    "sync_business_days",
    "sync_calendar_days",
    "sync_end_date",
    "sync_ipca_month_start",
    "sync_ipca_months",
    "sync_months",
    "sync_start_date",
]
