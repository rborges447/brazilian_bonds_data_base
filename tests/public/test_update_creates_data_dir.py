from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.public import read_data, update
from app.repositories.cdi import CdiRepository
from app.services.update_database_service import UpdateDatabaseResult

_EMPTY_GAPS: dict[str, dict[str, list[str]]] = {"bronze": {}, "silver": {}, "gold": {}}


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync")
def test_update_creates_package_layout(
    mock_sync,
    mock_status,
    tmp_path: Path,
) -> None:
    root = tmp_path / "pkg"

    result = update(data_root=str(root), force=False)

    mock_sync.assert_not_called()
    assert isinstance(result, UpdateDatabaseResult)
    assert result.environment is not None
    assert result.data_root == root
    assert result.skipped_sync is True
    assert result.sync_ran is False
    assert result.migration.total_applied

    env = result.environment
    for path in (
        env.database_dir,
        env.bronze_root,
        env.silver_root,
        env.gold_root,
        env.logs_dir,
        env.metadata_dir,
    ):
        assert path.is_dir()
    assert env.sqlite_db_path.is_file()


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync")
def test_update_then_read_data_without_goldreader_import(
    mock_sync,
    mock_status,
    tmp_path: Path,
) -> None:
    root = tmp_path / "consumer_pkg"

    result = update(data_root=str(root), force=False)
    mock_sync.assert_not_called()

    CdiRepository().upsert(
        pd.DataFrame([{"data_referencia": "2026-01-02", "cdi": 0.01}]),
        db_path=result.db_path,
    )

    data = read_data(data_root=str(root))
    assert len(data.cdi.fetch_all()) == 1
    assert hasattr(data, "cdi")
    assert hasattr(data, "ptax")
