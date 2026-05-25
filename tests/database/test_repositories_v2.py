from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.database import MIGRATIONS_DIR, apply_migrations
from app.repositories.cdi import CdiRepository
from app.repositories.feriados import FeriadosRepository
from app.repositories.ipca_dict import IpcaDictRepository


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
