"""Database connection helpers (SQLite today; PostgreSQL-ready)."""

from __future__ import annotations

import sqlite3
from enum import Enum
from pathlib import Path
from typing import Any

from app.config import get_settings


class Dialect(str, Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"


def get_dialect() -> Dialect:
    """Return active dialect; PostgreSQL when DATABASE_URL is wired in settings."""
    url = getattr(get_settings(), "database_url", None)
    if url and str(url).startswith(("postgresql://", "postgres://")):
        return Dialect.POSTGRES
    return Dialect.SQLITE


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open SQLite connection; creates parent dirs for the DB file."""
    if get_dialect() == Dialect.POSTGRES:
        raise NotImplementedError("PostgreSQL connection is not implemented yet.")
    path = Path(db_path) if db_path is not None else get_settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def execute_script(conn: sqlite3.Connection, sql: str) -> None:
    conn.executescript(sql)


def execute(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] | dict[str, Any] = (),
) -> sqlite3.Cursor:
    return conn.execute(sql, params)


def commit(conn: sqlite3.Connection) -> None:
    conn.commit()
