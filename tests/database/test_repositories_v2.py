from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from app.database import MIGRATIONS_DIR, apply_migrations
from app.database.schema import VNA_COLUMNS, validate_dataframe_columns
from app.repositories.cdi import CdiRepository
from app.repositories.feriados import FeriadosRepository
from app.repositories.ipca_dict import IpcaDictRepository
from app.repositories.vna import VnaRepository


def _migrate(db: Path) -> None:
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)


def test_feriados_replace_snapshot(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    _migrate(db)
    repo = FeriadosRepository()
    n = repo.replace_all(["2026-01-01", "2026-12-25"], db_path=db)
    assert n == 2
    assert repo.list_dates(db_path=db) == ["2026-01-01", "2026-12-25"]
    n2 = repo.replace_all(["2026-05-01"], db_path=db)
    assert n2 == 1
    assert repo.list_dates(db_path=db) == ["2026-05-01"]


def test_cdi_upsert(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    _migrate(db)
    df = pd.DataFrame(
        [{"data_referencia": "2026-05-15", "cdi": 0.05}],
    )
    n = CdiRepository().upsert(df, db_path=db)
    assert n == 1


def test_ipca_dict_upsert_minimal(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    _migrate(db)
    from app.database.schema import IPCA_DICT_COLUMNS

    row = {c: None for c in IPCA_DICT_COLUMNS}
    row["data_referencia"] = "2026-05-15"
    row["usa_fechado"] = 0
    df = pd.DataFrame([row])
    n = IpcaDictRepository().upsert(df, db_path=db)
    assert n == 1


def _vna_row(**overrides: object) -> dict:
    row = {
        "data_referencia": "2025-05-26",
        "codigo_selic": 210100,
        "tipo_correcao": "O",
        "index": 14.65,
        "data_validade": "2025-05-23",
        "vna": 16616.59,
        "vna_ajustado": None,
    }
    row.update(overrides)
    return row


def test_vna_upsert_two_titles_same_day(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    _migrate(db)
    df = pd.DataFrame(
        [
            _vna_row(codigo_selic=210100),
            _vna_row(codigo_selic=210200, vna=17000.0),
        ]
    )
    n = VnaRepository().upsert(df, db_path=db)
    assert n == 2
    conn = sqlite3.connect(db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM VNA").fetchone()[0]
        assert count == 2
    finally:
        conn.close()


def test_vna_upsert_replaces_same_key(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    _migrate(db)
    repo = VnaRepository()
    repo.upsert(pd.DataFrame([_vna_row(vna=100.0)]), db_path=db)
    repo.upsert(pd.DataFrame([_vna_row(vna=200.0)]), db_path=db)
    conn = sqlite3.connect(db)
    try:
        vna = conn.execute("SELECT vna FROM VNA WHERE codigo_selic = 210100").fetchone()[0]
        assert vna == 200.0
    finally:
        conn.close()


def test_vna_upsert_null_vna_ajustado(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    _migrate(db)
    VnaRepository().upsert(pd.DataFrame([_vna_row(vna_ajustado=None)]), db_path=db)
    conn = sqlite3.connect(db)
    try:
        val = conn.execute("SELECT vna_ajustado FROM VNA").fetchone()[0]
        assert val is None
    finally:
        conn.close()


def test_vna_upsert_rejects_bad_columns(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    _migrate(db)
    bad_extra = pd.DataFrame([{**_vna_row(), "extra": 1}])
    with pytest.raises(ValueError, match="unexpected columns"):
        validate_dataframe_columns(VnaRepository.table_name, bad_extra, VNA_COLUMNS)

    bad_missing = pd.DataFrame([{"data_referencia": "2025-05-26", "vna": 1.0}])
    with pytest.raises(ValueError, match="missing columns"):
        validate_dataframe_columns(VnaRepository.table_name, bad_missing, VNA_COLUMNS)
