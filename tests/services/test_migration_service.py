from __future__ import annotations

import sqlite3
from pathlib import Path

from app.database import BUSINESS_TABLES_V2
from app.services.migration_service import run_migrations


def test_run_migrations_creates_schema_on_empty_db(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    result = run_migrations(db_path=db)

    assert result.db_path == db
    assert len(result.newly_applied) > 0
    assert len(result.total_applied) == len(result.newly_applied)

    conn = sqlite3.connect(db)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {r[0] for r in rows}
        for table in BUSINESS_TABLES_V2:
            assert table in names
        assert "schema_migrations" in names
    finally:
        conn.close()


def test_run_migrations_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    first = run_migrations(db_path=db)
    second = run_migrations(db_path=db)

    assert second.newly_applied == ()
    assert second.total_applied == first.total_applied


def test_run_migrations_with_data_root(tmp_path: Path) -> None:
    result = run_migrations(data_root="pkg", base=tmp_path)

    expected_db = tmp_path / "pkg" / "database" / "app.db"
    assert result.db_path == expected_db
    assert expected_db.is_file()
    assert len(result.total_applied) > 0


def test_run_migrations_db_path_precedence(tmp_path: Path) -> None:
    custom_db = tmp_path / "custom.db"
    other_root_db = tmp_path / "pkg" / "database" / "app.db"

    result = run_migrations(db_path=custom_db, data_root="pkg", base=tmp_path)

    assert result.db_path == custom_db
    assert custom_db.is_file()
    assert not other_root_db.is_file()
