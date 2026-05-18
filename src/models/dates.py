"""Date utilities for pipeline task resolution."""

from __future__ import annotations

from datetime import date, timedelta


def iso_month_first(year: int, month: int) -> str:
    """First calendar day of a month as YYYY-MM-01."""
    return f"{year:04d}-{month:02d}-01"


def _month_start_from_iso(value: str) -> date:
    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return date(int(text[:4]), int(text[5:7]), 1)
    if len(text) >= 7 and text[4] == "-":
        return date(int(text[:4]), int(text[5:7]), 1)
    raise ValueError(f"Invalid date for month range: {value!r}")


def months_in_range(start: str, end: str) -> list[str]:
    """Inclusive calendar months from start through end as YYYY-MM-01."""
    start_dt = _month_start_from_iso(start)
    end_dt = _month_start_from_iso(end)
    if start_dt > end_dt:
        return []
    out: list[str] = []
    year, month = start_dt.year, start_dt.month
    while (year, month) <= (end_dt.year, end_dt.month):
        out.append(iso_month_first(year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return out


def business_days(start: str, end: str, skip_weekends: bool = True) -> list[str]:
    """Inclusive range of ISO dates from start through end."""
    start_dt = date.fromisoformat(start)
    end_dt = date.fromisoformat(end)
    if start_dt > end_dt:
        return []
    out: list[str] = []
    cur = start_dt
    while cur <= end_dt:
        if (not skip_weekends) or cur.weekday() < 5:
            out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out
