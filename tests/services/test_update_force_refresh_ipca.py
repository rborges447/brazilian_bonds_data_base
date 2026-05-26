"""Integration tests for force refresh IPCA invalidation (FR-009)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from app.database import MIGRATIONS_DIR, apply_migrations
from app.database.connection import get_connection
from app.database.schema import IPCA_DICT_COLUMNS
from app.repositories.ipca_dict import IpcaDictRepository
from app.services.local_environment_service import ensure_local_environment
from app.services.migration_service import MigrationRunResult
from app.services.update_database_service import update_database

_EMPTY_GAPS: dict[str, dict[str, list[str]]] = {"bronze": {}, "silver": {}, "gold": {}}


def _migration_stub(db_path: Path) -> MigrationRunResult:
    return MigrationRunResult(db_path=db_path, newly_applied=(), total_applied=("001",))


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"test")


def _sql_dates(db: Path) -> list[str]:
    conn = get_connection(db)
    try:
        cur = conn.execute(
            "SELECT data_referencia FROM IPCA_DICT ORDER BY data_referencia"
        )
        return [str(row[0])[:10] for row in cur.fetchall()]
    finally:
        conn.close()


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync", return_value=[])
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_force_ipca_invalidates_month_and_daily_series(
    mock_migrations,
    mock_sync,
    mock_status,
    tmp_path: Path,
) -> None:
    root = tmp_path / "pkg"
    env = ensure_local_environment(data_root=root, create=True)
    ref = "2026-05-20"
    end = "2026-05-22"

    ipca_silver = (
        env.silver_root / "ipca_indice" / "reference_month=2026-05-01" / "part.parquet"
    )
    _touch(ipca_silver)

    apply_migrations(db_path=env.sqlite_db_path, migrations_dir=MIGRATIONS_DIR)
    rows = []
    for day in ("2026-05-01", "2026-05-20", "2026-05-22", "2026-05-26"):
        row = {c: None for c in IPCA_DICT_COLUMNS}
        row["data_referencia"] = day
        row["usa_fechado"] = 0
        rows.append(row)
    IpcaDictRepository().upsert(pd.DataFrame(rows), db_path=env.sqlite_db_path)

    result = update_database(
        data_root=str(root),
        datasets=["ipca_indice"],
        start_date=ref,
        end_date=end,
        refresh_dates=[ref],
        force=True,
    )

    assert result.invalidation is not None
    assert not ipca_silver.is_file()
    assert _sql_dates(env.sqlite_db_path) == ["2026-05-26"]
    mock_sync.assert_called_once()
    assert mock_sync.call_args.kwargs["ipca_dict_dates"] is not None
    assert mock_sync.call_args.kwargs["ipca_dict_dates"][0] == "2026-05-01"
    assert mock_sync.call_args.kwargs["ipca_dict_dates"][-1] == end


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync", return_value=[])
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_force_ipca_passes_full_rebuild_dates_to_sync(
    mock_migrations,
    mock_sync,
    mock_status,
    tmp_path: Path,
) -> None:
    root = tmp_path / "pkg2"
    ensure_local_environment(data_root=root, create=True)
    apply_migrations(
        db_path=root / "database" / "app.db", migrations_dir=MIGRATIONS_DIR
    )

    update_database(
        data_root=str(root),
        datasets=None,
        start_date="2026-05-24",
        end_date="2026-05-26",
        refresh_dates=["2026-05-24"],
        force=True,
    )

    ipca_dates = mock_sync.call_args.kwargs.get("ipca_dict_dates")
    assert ipca_dates is not None
    assert ipca_dates[0] == "2026-05-01"
    assert ipca_dates[-1] == "2026-05-26"
