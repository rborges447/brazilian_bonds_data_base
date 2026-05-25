from __future__ import annotations

import sqlite3
from pathlib import Path

from app.database import BUSINESS_TABLES_V2, MIGRATIONS_DIR, apply_migrations


def test_apply_migrations_creates_tables(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)

    conn = sqlite3.connect(db)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {r[0] for r in rows}
        for table in BUSINESS_TABLES_V2:
            assert table in names, f"missing table {table}"
        assert "job_runs" in names
        assert "schema_migrations" in names
        assert "IPCA_INDICE" not in names
        assert "PROJECOES" not in names
    finally:
        conn.close()
