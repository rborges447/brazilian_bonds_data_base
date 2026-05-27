from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.database import MIGRATIONS_DIR, apply_migrations
from app.database.readers import GoldReader
from app.lake.gold.contracts import GoldMaterialized
from app.repositories.vna import VnaRepository
from app.services.gold_persistence import persist_materialized


def _migrate(db: Path) -> None:
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)


def _vna_gold_row(**overrides: object) -> dict:
    row = {
        "data_referencia": "2025-05-26",
        "codigo_selic": 210100,
        "tipo_correcao": "O",
        "index": 14.65,
        "data_validade": "2025-05-23",
        "vna": 16616.592308,
        "vna_ajustado": None,
    }
    row.update(overrides)
    return row


def test_persist_vna(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    _migrate(db)
    df = pd.DataFrame([_vna_gold_row()])
    result = GoldMaterialized(name="vna", silver={}, value=df)
    n = persist_materialized(result, db_path=db)
    assert n == 1
    reader = GoldReader(db_path=db)
    out = reader.vna.fetch_on("2025-05-26")
    assert len(out) == 1
    assert out.iloc[0]["codigo_selic"] == 210100
