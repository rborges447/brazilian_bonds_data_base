"""SIDRA API period strings from calendar range."""

from __future__ import annotations

from datetime import date

from app.core.dates import months_in_range


def sidra_period_from_dates(start: date, end: date) -> str:
    """
    Build sidrapy ``period`` covering inclusive calendar months [start, end].

    Uses ``last N`` where N is the number of months in range (minimum 2).
    """
    if start > end:
        raise ValueError(f"start must be <= end, got {start} > {end}")
    months = months_in_range(start.isoformat(), end.isoformat())
    n = max(len(months), 2)
    return f"last {n}"


def sidra_period_for_sync() -> str:
    """Period from IPCA lookback month through sync end (covers fechado M-1)."""
    from app.core.sync_range import sync_end_date, sync_ipca_month_start

    return sidra_period_from_dates(
        date.fromisoformat(sync_ipca_month_start()),
        date.fromisoformat(sync_end_date()),
    )
