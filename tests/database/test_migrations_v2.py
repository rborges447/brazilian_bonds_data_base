from __future__ import annotations

import sqlite3
from pathlib import Path

from app.database import BUSINESS_TABLES_V2, MIGRATIONS_DIR, apply_migrations
from app.database.schema import TABLE_VNA


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


def test_vna_table_schema(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)

    conn = sqlite3.connect(db)
    try:
        assert TABLE_VNA in BUSINESS_TABLES_V2
        cols = conn.execute(f"PRAGMA table_info({TABLE_VNA})").fetchall()
        assert len(cols) == 7
        col_names = [c[1] for c in cols]
        assert col_names == [
            "data_referencia",
            "codigo_selic",
            "tipo_correcao",
            "index",
            "data_validade",
            "vna",
            "vna_ajustado",
        ]
        pk_cols = [c[1] for c in cols if c[5] > 0]
        assert pk_cols == ["data_referencia", "codigo_selic"]
    finally:
        conn.close()
