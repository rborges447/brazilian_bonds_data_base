"""SQL helpers for dialect portability."""

from __future__ import annotations

from app.database.connection import Dialect, get_dialect


def upsert_prefix(dialect: Dialect | None = None) -> str:
    """Return INSERT prefix for upsert (SQLite OR REPLACE; PG uses ON CONFLICT later)."""
    if (dialect or get_dialect()) == Dialect.POSTGRES:
        raise NotImplementedError("PostgreSQL upsert is not implemented yet.")
    return "INSERT OR REPLACE INTO"
