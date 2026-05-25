"""Read persisted gold holidays (FERIADOS)."""

from __future__ import annotations


def read_feriados_gold() -> list[str]:
    """
    Return ISO holiday dates from gold SQLite FERIADOS table.

    Returns an empty list when the table has no rows (first pipeline run).
    """
    try:
        from app.repositories.feriados import FeriadosRepository

        return FeriadosRepository().list_dates()
    except Exception:
        return []
