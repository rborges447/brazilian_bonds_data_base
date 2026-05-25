"""Run SQLite schema migrations (facade over app.database.migrate)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.database.connection import get_connection
from app.database.migrate import apply_migrations
from app.services.local_environment_service import ensure_local_environment


@dataclass(frozen=True)
class MigrationRunResult:
    db_path: Path
    newly_applied: tuple[str, ...]
    total_applied: tuple[str, ...]


def _resolve_db_path(
    *,
    db_path: str | Path | None,
    data_root: str | Path | None,
    base: Path | None,
) -> Path:
    if db_path is not None:
        return Path(db_path)
    if data_root is not None:
        env = ensure_local_environment(data_root, base=base, create=True)
        return env.sqlite_db_path
    return get_settings().db_path


def _read_applied_versions(db_path: Path) -> set[str]:
    conn = get_connection(db_path)
    try:
        try:
            rows = conn.execute("SELECT version FROM schema_migrations;").fetchall()
        except sqlite3.OperationalError:
            return set()
        return {str(r[0]) for r in rows}
    finally:
        conn.close()


def run_migrations(
    *,
    db_path: str | Path | None = None,
    data_root: str | Path | None = None,
    migrations_dir: Path | None = None,
    base: Path | None = None,
) -> MigrationRunResult:
    """Apply pending migrations idempotently; return versions applied in this run."""
    resolved_db = _resolve_db_path(db_path=db_path, data_root=data_root, base=base)
    directory = migrations_dir or get_settings().migrations_dir

    applied_before = _read_applied_versions(resolved_db)
    apply_migrations(db_path=resolved_db, migrations_dir=directory)
    applied_after = _read_applied_versions(resolved_db)

    newly = tuple(sorted(applied_after - applied_before))
    total = tuple(sorted(applied_after))
    return MigrationRunResult(
        db_path=resolved_db,
        newly_applied=newly,
        total_applied=total,
    )
