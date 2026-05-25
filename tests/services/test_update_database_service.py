from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import get_settings
from app.services.local_environment_service import ensure_local_environment
from app.services.migration_service import MigrationRunResult
from app.services.sync_runner import SyncPhaseResult
from app.services.update_database_service import update_database

_EMPTY_GAPS: dict[str, dict[str, list[str]]] = {"bronze": {}, "silver": {}, "gold": {}}


def _migration_stub(db_path: Path) -> MigrationRunResult:
    return MigrationRunResult(db_path=db_path, newly_applied=(), total_applied=("001",))


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync")
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_dev_layout_runs_migrations(
    mock_migrations,
    mock_sync,
    mock_status,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()

    result = update_database(force=False)

    assert result.environment is None
    assert result.db_path == get_settings().db_path
    mock_migrations.assert_called_once()
    mock_sync.assert_not_called()
    assert result.skipped_sync is True
    assert result.sync_ran is False


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync")
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_skips_sync_when_no_gaps(
    mock_migrations,
    mock_sync,
    mock_status,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()

    result = update_database(force=False)

    assert result.skipped_sync is True
    mock_sync.assert_not_called()


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch(
    "app.services.update_database_service.run_daily_sync",
    return_value=[
        SyncPhaseResult(name="bronze", task_count=0, details=[]),
        SyncPhaseResult(name="silver", task_count=0, details=[]),
        SyncPhaseResult(name="gold", task_count=0, details=[]),
    ],
)
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_force_runs_sync(
    mock_migrations,
    mock_sync,
    mock_status,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()

    result = update_database(force=True)

    assert result.skipped_sync is False
    assert result.sync_ran is True
    mock_sync.assert_called_once()


def test_update_package_overlay_paths(tmp_path: Path) -> None:
    get_settings.cache_clear()
    env = ensure_local_environment(data_root=tmp_path / "pkg", create=False)
    settings = get_settings()
    settings.activate_path_overlay(env)
    try:
        assert settings.bronze_root == tmp_path / "pkg" / "lake" / "bronze"
        assert settings.silver_root == tmp_path / "pkg" / "lake" / "silver"
        assert settings.db_path == tmp_path / "pkg" / "database" / "app.db"
    finally:
        settings.deactivate_path_overlay()


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync")
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_overlay_restored_after_update(
    mock_migrations,
    mock_sync,
    mock_status,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "dev"))
    get_settings.cache_clear()
    dev_bronze = get_settings().bronze_root

    update_database(data_root=str(tmp_path / "pkg"), base=tmp_path, force=False)

    assert get_settings().bronze_root == dev_bronze
    assert get_settings()._path_overlay is None
