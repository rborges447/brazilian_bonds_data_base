from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from app.config import get_settings
from app.database import MIGRATIONS_DIR, apply_migrations
from app.database.connection import get_connection
from app.repositories.bmf import BmfRepository
from app.repositories.cdi import CdiRepository
from app.services.local_environment_service import ensure_local_environment
from app.services.migration_service import MigrationRunResult
from app.services.sync_runner import SyncPhaseResult
from app.services.pipeline_invalidation import InvalidationRunResult
from app.services.update_database_service import update_database

_EMPTY_GAPS: dict[str, dict[str, list[str]]] = {"bronze": {}, "silver": {}, "gold": {}}
_EMPTY_INVALIDATION = InvalidationRunResult(
    bronze_files_removed=0,
    silver_files_removed=0,
    gold_rows_deleted=0,
)


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
    "app.services.update_database_service.run_pipeline_invalidation",
    return_value=(None, _EMPTY_INVALIDATION),
)
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
    mock_invalidation,
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


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync")
@patch("app.services.update_database_service.run_pipeline_invalidation")
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_force_false_skips_invalidation(
    mock_migrations,
    mock_invalidation,
    mock_sync,
    mock_status,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()

    result = update_database(force=False)

    mock_invalidation.assert_not_called()
    assert result.invalidation is None


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_force_true_runs_invalidation_before_sync(
    mock_migrations,
    mock_status,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_order: list[str] = []

    def _invalidation(**_kwargs: object) -> tuple[None, InvalidationRunResult]:
        call_order.append("invalidation")
        return None, _EMPTY_INVALIDATION

    def _sync(*_args: object, **_kwargs: object) -> list[SyncPhaseResult]:
        call_order.append("sync")
        return []

    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()

    with patch(
        "app.services.update_database_service.run_pipeline_invalidation",
        side_effect=_invalidation,
    ), patch(
        "app.services.update_database_service.run_daily_sync",
        side_effect=_sync,
    ):
        update_database(force=True)

    assert call_order == ["invalidation", "sync"]


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync", return_value=[])
@patch(
    "app.services.update_database_service.run_pipeline_invalidation",
    return_value=(
        None,
        InvalidationRunResult(
            bronze_files_removed=1,
            silver_files_removed=2,
            gold_rows_deleted=3,
        ),
    ),
)
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_force_true_sets_invalidation_on_result(
    mock_migrations,
    mock_invalidation,
    mock_sync,
    mock_status,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()

    result = update_database(force=True)

    assert result.invalidation is not None
    assert result.invalidation.bronze_files_removed == 1
    assert result.invalidation.silver_files_removed == 2
    assert result.invalidation.gold_rows_deleted == 3


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync", return_value=[])
@patch(
    "app.services.update_database_service.run_pipeline_invalidation",
    return_value=(None, _EMPTY_INVALIDATION),
)
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_passes_refresh_dates_to_invalidation(
    mock_migrations,
    mock_invalidation,
    mock_sync,
    mock_status,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()

    update_database(force=True, refresh_dates=["2026-05-25"])

    mock_invalidation.assert_called_once()
    assert mock_invalidation.call_args.kwargs["refresh_dates"] == ["2026-05-25"]


_REF_DATE = "2026-05-25"


def _touch_partition(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"test")


@patch("app.services.update_database_service.sync_status_report", return_value=_EMPTY_GAPS)
@patch("app.services.update_database_service.run_daily_sync", return_value=[])
@patch("app.services.update_database_service.run_migrations", side_effect=_migration_stub)
def test_update_force_datasets_cdi_does_not_invalidate_bmf(
    mock_migrations,
    mock_sync,
    mock_status,
    tmp_path: Path,
) -> None:
    root = tmp_path / "pkg"
    env = ensure_local_environment(data_root=root, create=True)
    ref = _REF_DATE

    cdi_bronze = env.bronze_root / "cdi" / f"data={ref}" / "part.parquet"
    cdi_silver = env.silver_root / "cdi" / f"data={ref}" / "part.parquet"
    bmf_bronze = env.bronze_root / "ajustes_bmf" / f"data={ref}" / "part.parquet"
    bmf_silver = env.silver_root / "ajustes_bmf" / f"data={ref}" / "part.parquet"
    for path in (cdi_bronze, cdi_silver, bmf_bronze, bmf_silver):
        _touch_partition(path)

    apply_migrations(db_path=env.sqlite_db_path, migrations_dir=MIGRATIONS_DIR)

    CdiRepository().upsert(
        pd.DataFrame([{"data_referencia": ref, "cdi": 0.01}]),
        db_path=env.sqlite_db_path,
    )
    BmfRepository().upsert(
        pd.DataFrame(
            [
                {
                    "ticker": "DI1F27",
                    "codigo_isin": None,
                    "data_vencimento": "2027-01-01",
                    "data_referencia": ref,
                    "taxa_ajuste": 0.0,
                    "quantidade_ajuste": 1.0,
                }
            ]
        ),
        db_path=env.sqlite_db_path,
    )

    result = update_database(
        data_root=str(root),
        datasets=["cdi"],
        start_date=ref,
        end_date=ref,
        refresh_dates=[ref],
        force=True,
    )

    assert result.sync_ran is True
    assert result.invalidation is not None
    assert result.invalidation.bronze_files_removed == 1
    assert result.invalidation.silver_files_removed == 1
    assert result.invalidation.gold_rows_deleted == 1
    assert not cdi_bronze.is_file()
    assert not cdi_silver.is_file()
    assert bmf_bronze.is_file()
    assert bmf_silver.is_file()

    conn = get_connection(env.sqlite_db_path)
    try:
        cdi_count = conn.execute(
            "SELECT COUNT(*) FROM CDI WHERE data_referencia = ?", (ref,)
        ).fetchone()[0]
        bmf_count = conn.execute(
            "SELECT COUNT(*) FROM AJUSTES_BMF WHERE data_referencia = ?", (ref,)
        ).fetchone()[0]
    finally:
        conn.close()

    assert cdi_count == 0
    assert bmf_count == 1
