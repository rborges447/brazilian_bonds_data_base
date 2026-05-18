"""Shared helpers for data providers."""

from __future__ import annotations

from datetime import date, datetime
from typing import Union

DateInput = Union[str, date, datetime]


def ensure_date(data_ref: DateInput) -> date:
    """Coerce input to datetime.date (YYYY-MM-DD string or date)."""
    if isinstance(data_ref, date) and not isinstance(data_ref, datetime):
        return data_ref
    if isinstance(data_ref, datetime):
        return data_ref.date()
    if isinstance(data_ref, str):
        try:
            return datetime.strptime(data_ref, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("data_ref must be 'YYYY-MM-DD' (e.g. '2025-08-01').") from exc
    raise TypeError("data_ref must be str ('YYYY-MM-DD') or datetime.date.")
