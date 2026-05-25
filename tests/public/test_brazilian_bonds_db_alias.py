from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.database import MIGRATIONS_DIR, apply_migrations
from app.repositories.cdi import CdiRepository


def _migrate(db: Path) -> None:
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)


def test_import_alias() -> None:
    import brazilian_bonds_db as bbdb

    assert hasattr(bbdb, "update")
    assert hasattr(bbdb, "read_data")
    assert callable(bbdb.update)
    assert callable(bbdb.read_data)


def test_readers_module_import_read_data() -> None:
    from brazilian_bonds_db.readers import read_data

    assert callable(read_data)


def test_alias_all_surface() -> None:
    import brazilian_bonds_db

    assert set(brazilian_bonds_db.__all__) == {"read_data", "update"}
    assert not hasattr(brazilian_bonds_db, "GoldReader")
    assert not hasattr(brazilian_bonds_db, "read_gold")


def test_from_package_import_read_data() -> None:
    from brazilian_bonds_db import read_data

    assert callable(read_data)


def test_alias_delegates_to_app_public() -> None:
    import brazilian_bonds_db as bbdb
    from app.public.readers import read_data as public_read_data
    from app.public.update import update as public_update
    from brazilian_bonds_db.readers import read_data as readers_read_data
    from brazilian_bonds_db.update import update as module_update

    assert bbdb.update is public_update
    assert bbdb.read_data is public_read_data
    assert module_update is public_update
    assert readers_read_data is public_read_data


@patch("app.services.update_database_service.update_database")
def test_import_alias_does_not_run_update(mock_update_database) -> None:
    for name in list(sys.modules):
        if name == "brazilian_bonds_db" or name.startswith("brazilian_bonds_db."):
            del sys.modules[name]
    importlib.import_module("brazilian_bonds_db")
    mock_update_database.assert_not_called()


def test_read_data_via_alias_returns_datasets(tmp_path: Path) -> None:
    import brazilian_bonds_db as bbdb

    db = tmp_path / "alias_read.db"
    _migrate(db)
    CdiRepository().upsert(
        pd.DataFrame([{"data_referencia": "2026-01-02", "cdi": 0.01}]),
        db_path=db,
    )

    data = bbdb.read_data(db_path=db)
    assert len(data.cdi.fetch_all()) == 1
    assert hasattr(data, "cdi")
    assert hasattr(data, "ptax")
