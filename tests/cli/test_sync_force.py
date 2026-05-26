"""CLI force refresh flags for run_sync daily."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.cli.sync import DailyOptions, _parse_daily_args, cmd_daily
from app.services.migration_service import MigrationRunResult
from app.services.pipeline_invalidation import InvalidationRunResult
from app.services.sync_runner import SyncPhaseResult
from app.services.update_database_service import UpdateDatabaseResult


def _empty_update_result() -> UpdateDatabaseResult:
    return UpdateDatabaseResult(
        data_root=None,
        db_path=Path("test.db"),
        environment=None,
        migration=MigrationRunResult(db_path=Path("test.db"), newly_applied=(), total_applied=()),
        gaps_before={"bronze": {}, "silver": {}, "gold": {}},
        gaps_after={"bronze": {}, "silver": {}, "gold": {}},
        sync_ran=True,
        sync_phases=(
            SyncPhaseResult(name="bronze", task_count=0, details=[]),
            SyncPhaseResult(name="silver", task_count=0, details=[]),
            SyncPhaseResult(name="gold", task_count=0, details=[]),
        ),
        skipped_sync=False,
        invalidation=InvalidationRunResult(
            bronze_files_removed=1,
            silver_files_removed=2,
            gold_rows_deleted=3,
        ),
    )


@patch("app.cli.sync.print_silver_results")
@patch("app.cli.sync.print_bronze_results")
@patch("app.cli.sync.run_daily_sync")
@patch("app.cli.sync.update_database")
@patch("app.cli.sync.cmd_status", return_value=0)
def test_daily_without_force_calls_run_daily_sync_only(
    mock_status: MagicMock,
    mock_update: MagicMock,
    mock_sync: MagicMock,
    mock_print_bronze: MagicMock,
    mock_print_silver: MagicMock,
) -> None:
    mock_sync.return_value = [
        SyncPhaseResult(name="bronze", task_count=0, details=[]),
        SyncPhaseResult(name="silver", task_count=0, details=[]),
        SyncPhaseResult(name="gold", task_count=0, details=[]),
    ]

    code = cmd_daily(DailyOptions(
        end_date="2026-05-25",
        do_persist=True,
        force=False,
        start_date=None,
        datasets=None,
        refresh_dates=None,
    ))

    assert code == 0
    mock_sync.assert_called_once_with("2026-05-25", persist=True)
    mock_update.assert_not_called()


@patch("app.cli.sync.print_silver_results")
@patch("app.cli.sync.print_bronze_results")
@patch("app.cli.sync.run_daily_sync")
@patch("app.cli.sync.update_database", return_value=_empty_update_result())
@patch("app.cli.sync.cmd_status", return_value=0)
def test_daily_with_force_delegates_to_update_database(
    mock_status: MagicMock,
    mock_update: MagicMock,
    mock_sync: MagicMock,
    mock_print_bronze: MagicMock,
    mock_print_silver: MagicMock,
) -> None:
    code = cmd_daily(DailyOptions(
        end_date="2026-05-25",
        do_persist=True,
        force=True,
        start_date="2026-05-01",
        datasets=["ajustes_bmf"],
        refresh_dates=["2026-05-25"],
    ))

    assert code == 0
    mock_sync.assert_not_called()
    mock_update.assert_called_once_with(
        force=True,
        persist=True,
        start_date="2026-05-01",
        end_date="2026-05-25",
        datasets=["ajustes_bmf"],
        refresh_dates=["2026-05-25"],
    )


def test_parse_refresh_dates_without_force_is_ignored(capsys: pytest.CaptureFixture[str]) -> None:
    options = _parse_daily_args(["2026-05-25", "--refresh-dates", "2026-05-25"])

    assert options.force is False
    assert options.refresh_dates is None
    assert "ignored without --force" in capsys.readouterr().err


def test_parse_daily_args_csv_lists() -> None:
    options = _parse_daily_args([
        "2026-05-25",
        "--force",
        "--datasets",
        "cdi, ajustes_bmf",
        "--refresh-dates",
        "2026-05-24,2026-05-25",
    ])

    assert options.datasets == ["cdi", "ajustes_bmf"]
    assert options.refresh_dates == ["2026-05-24", "2026-05-25"]
