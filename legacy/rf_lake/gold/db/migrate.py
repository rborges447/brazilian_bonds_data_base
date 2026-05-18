from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from rf_lake.gold.db.connection import get_conn
from rf_lake.settings import MIGRATIONS_DIR


@dataclass(frozen=True)
class Migration:
    version: str
    path: Path


def _ensure_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL
        );
    """)


def _applied(conn) -> set[str]:
    _ensure_table(conn)
    rows = conn.execute("SELECT version FROM schema_migrations;").fetchall()
    return {r[0] for r in rows}


def _list_files(dirpath: Path) -> List[Migration]:
    files = sorted(dirpath.glob("*.sql"))  # sort by filename (001..., 002...)
    out: List[Migration] = []
    for p in files:
        version = p.name.split("_", 1)[0]
        out.append(Migration(version=version, path=p))
    return out


def apply_migrations(db_path=None, migrations_dir: Path = MIGRATIONS_DIR) -> None:
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    conn = get_conn(db_path)
    try:
        _ensure_table(conn)
        applied = _applied(conn)

        for m in _list_files(migrations_dir):
            if m.version in applied:
                continue

            sql = m.path.read_text(encoding="utf-8")
            try:
                # executescript manages transactions internally
                conn.executescript(sql)

                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?);",
                    (m.version, datetime.now(timezone.utc).isoformat()),
                )
                conn.commit()
                print(f"Applied {m.path.name}")

            except Exception as e:
                # SQLite's executescript commits automatically, so rollback may not be needed
                # But we try anyway and ignore if there's no transaction
                try:
                    conn.rollback()
                except sqlite3.OperationalError:
                    pass
                raise

    finally:
        conn.close()


if __name__ == "__main__":
    apply_migrations()
