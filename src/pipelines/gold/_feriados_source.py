"""Read persisted gold holidays (FERIADOS). Empty until SQL gold layer is wired."""

from __future__ import annotations


def read_feriados_gold() -> list[str]:
    """
    Return ISO holiday dates from gold persistence.

    Returns an empty list when gold DB is not configured or FERIADOS has no rows
    (first pipeline run).
    """
    return []
