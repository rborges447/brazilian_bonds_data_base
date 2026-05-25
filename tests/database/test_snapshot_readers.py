"""Snapshot datasets expose fetch_all only."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.database import MIGRATIONS_DIR, apply_migrations
from app.database.readers import GoldReader
from app.repositories.feriados import FeriadosRepository


def _migrate(db: Path) -> None:
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)


def test_feriados_fetch_all_only(tmp_path: Path) -> None:
    db = tmp_path / "read.db"
    _migrate(db)
    FeriadosRepository().upsert(
        pd.DataFrame([{"data": "2026-01-01"}, {"data": "2026-05-01"}]),
        db_path=db,
    )
    reader = GoldReader(db_path=db)
    assert len(reader.feriados.fetch_all()) == 2
    with pytest.raises(TypeError, match="fetch_all"):
        reader.feriados.fetch_latest(1)
    with pytest.raises(TypeError, match="fetch_all"):
        reader.feriados.fetch_on("2026-01-01")
