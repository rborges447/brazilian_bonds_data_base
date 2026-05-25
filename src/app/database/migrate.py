"""Apply versioned SQL migrations (ported from legacy rf_lake)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.database.connection import get_connection

_BUILTIN_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
MIGRATIONS_DIR = _BUILTIN_MIGRATIONS_DIR


@dataclass(frozen=True)
class Migration:
    version: str
    path: Path


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        """
    )


def _applied(conn: sqlite3.Connection) -> set[str]:
    _ensure_table(conn)
    rows = conn.execute("SELECT version FROM schema_migrations;").fetchall()
    return {r[0] for r in rows}


def _list_files(dirpath: Path) -> list[Migration]:
    out: list[Migration] = []
    for p in sorted(dirpath.glob("*.sql")):
        version = p.name.split("_", 1)[0]
        out.append(Migration(version=version, path=p))
    return out


def apply_migrations(
    db_path: Path | str | None = None,
    migrations_dir: Path | None = None,
) -> None:
    if migrations_dir is None:
        from app.config import get_settings

        migrations_dir = get_settings().migrations_dir
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    conn = get_connection(db_path)
    try:
        _ensure_table(conn)
        applied = _applied(conn)

        for m in _list_files(migrations_dir):
            if m.version in applied:
                continue

            sql = m.path.read_text(encoding="utf-8")
            try:
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?);",
                    (m.version, datetime.now(timezone.utc).isoformat()),
                )
                conn.commit()
                print(f"Applied {m.path.name}")
            except Exception:
                try:
                    conn.rollback()
                except sqlite3.OperationalError:
                    pass
                raise
    finally:
        conn.close()
