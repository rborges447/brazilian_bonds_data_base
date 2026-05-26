from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.migration_service import MigrationRunResult
from app.services.update_database_service import UpdateDatabaseResult

_EMPTY_GAPS: dict[str, dict[str, list[str]]] = {"bronze": {}, "silver": {}, "gold": {}}


def _result_stub(db_path: Path | None = None) -> UpdateDatabaseResult:
    path = db_path or Path("test.db")
    return UpdateDatabaseResult(
        data_root=None,
        db_path=path,
        environment=None,
        migration=MigrationRunResult(db_path=path, newly_applied=(), total_applied=()),
        gaps_before=_EMPTY_GAPS,
        gaps_after=_EMPTY_GAPS,
        sync_ran=False,
        sync_phases=(),
        skipped_sync=True,
        invalidation=None,
    )


@patch("app.public.update.update_database", return_value=_result_stub())
def test_update_delegates_to_update_database(mock_update_database) -> None:
    from app.public import update

    result = update(force=True, persist=False)

    mock_update_database.assert_called_once_with(
        data_root=None,
        datasets=None,
        start_date=None,
        end_date=None,
        force=True,
        persist=False,
        refresh_dates=None,
    )
    assert isinstance(result, UpdateDatabaseResult)
    assert result.skipped_sync is True


def test_update_rejects_unknown_kwargs() -> None:
    from app.public import update

    with pytest.raises(TypeError, match="unexpected keyword arguments"):
        update(foo=1)


@patch("app.public.update.update_database", return_value=_result_stub())
def test_update_with_data_root_passes_through(mock_update_database, tmp_path: Path) -> None:
    from app.public import update

    root = tmp_path / "pkg"
    update(data_root=str(root), force=False)

    mock_update_database.assert_called_once_with(
        data_root=str(root),
        datasets=None,
        start_date=None,
        end_date=None,
        force=False,
        persist=True,
        refresh_dates=None,
    )


@patch("app.public.update.update_database", return_value=_result_stub())
def test_update_passes_refresh_dates(mock_update_database) -> None:
    from app.public import update

    update(refresh_dates=["2026-05-25"], force=True)

    mock_update_database.assert_called_once_with(
        data_root=None,
        datasets=None,
        start_date=None,
        end_date=None,
        force=True,
        persist=True,
        refresh_dates=["2026-05-25"],
    )
