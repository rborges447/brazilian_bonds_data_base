from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.database import MIGRATIONS_DIR, apply_migrations
from app.public import read_data
from app.repositories.cdi import CdiRepository


def _migrate(db: Path) -> None:
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)


def test_read_data_delegates_to_gold_reader_with_db_path(tmp_path: Path) -> None:
    db = tmp_path / "read.db"
    _migrate(db)
    CdiRepository().upsert(
        pd.DataFrame(
            [
                {"data_referencia": "2026-01-02", "cdi": 0.01},
                {"data_referencia": "2026-01-03", "cdi": 0.02},
            ]
        ),
        db_path=db,
    )
    data = read_data(db_path=db)
    assert len(data.cdi.fetch_all()) == 2
    for attr in (
        "cdi",
        "ptax",
        "ipca_dict",
        "titulos_publicos",
        "mercado_secundario",
        "mercado_com_liquidacoes",
        "vna",
    ):
        assert hasattr(data, attr)


def test_read_data_resolves_data_root(tmp_path: Path) -> None:
    root = tmp_path / "pkg_data"
    env_db = root / "database" / "app.db"
    root.mkdir(parents=True)
    env_db.parent.mkdir(parents=True)
    _migrate(env_db)
    CdiRepository().upsert(
        pd.DataFrame([{"data_referencia": "2026-01-02", "cdi": 0.01}]),
        db_path=env_db,
    )
    data = read_data(data_root=str(root))
    assert len(data.cdi.fetch_all()) == 1


def test_read_data_rejects_unknown_kwargs(tmp_path: Path) -> None:
    db = tmp_path / "read.db"
    _migrate(db)
    with pytest.raises(TypeError, match="unexpected keyword arguments"):
        read_data(db_path=db, foo=1)
