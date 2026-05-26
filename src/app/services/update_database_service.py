"""Orchestrate local environment, migrations, gap detection, and daily sync."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.sync_verify import has_mandatory_gaps, sync_status_report
from app.services.local_environment_service import LocalEnvironment, ensure_local_environment
from app.services.migration_service import MigrationRunResult, run_migrations
from app.services.pipeline_invalidation import (
    InvalidationRunResult,
    run_pipeline_invalidation,
)
from app.services.sync_runner import SyncPhaseResult, run_daily_sync


@dataclass(frozen=True)
class UpdateDatabaseResult:
    data_root: Path | None
    db_path: Path
    environment: LocalEnvironment | None
    migration: MigrationRunResult
    gaps_before: dict[str, dict[str, list[str]]]
    gaps_after: dict[str, dict[str, list[str]]]
    sync_ran: bool
    sync_phases: tuple[SyncPhaseResult, ...]
    skipped_sync: bool
    invalidation: InvalidationRunResult | None = None


def update_database(
    *,
    data_root: str | Path | None = None,
    datasets: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    force: bool = False,
    persist: bool = True,
    refresh_dates: list[str] | None = None,
    base: Path | None = None,
) -> UpdateDatabaseResult:
    """Orchestrate local environment initialization, migrations and (optional) sync.

    Workflow (high level):
        1) Ensure/activate lake directories and point the current process to the
           resolved ``data_root`` layout (path overlay).
        2) Apply SQLite migrations.
        3) Compute gaps (``bronze``/``silver``/``gold``) via ``sync_status_report``.
        4) If ``force=True``, run pipeline invalidation in the selected scope
           *before* the daily sync (bronze/silver artifacts removed; gold SQLite
           rows deleted where applicable).
        5) Run the daily bronze → silver → gold sync.

    IPCA invariant:
        When the invalidation scope includes any of the monthly IPCA datasets
        (``ipca_indice``/``projecoes``), the invalidation step computes the daily
        calendar dates that must be rematerialized in gold ``ipca_dict``.
        The daily rebuild itself is performed by the existing gold builder logic
        (no business rule reimplementation here).

    Args:
        data_root: Root path for package layout (bronze/silver/gold under it).
        datasets: Optional dataset list to restrict invalidation+sync. ``None``
            means all pipeline datasets.
        start_date / end_date: Sync/invalidation window (YYYY-MM-DD).
        force: When ``True``, deletes artifacts in the resolved scope before sync.
        persist: Whether gold persistence is enabled during sync.
        refresh_dates: Optional explicit ISO dates to restrict daily invalidation
            to explicit dates within the window (only meaningful with ``force=True``).
        base: Optional base directory used to resolve relative ``data_root``.

    Returns:
        UpdateDatabaseResult with detailed gap reports and sync phase metadata.
    """
    settings = get_settings()
    env: LocalEnvironment | None = None
    if data_root is not None:
        env = ensure_local_environment(data_root, base=base, create=True)
        settings.activate_path_overlay(env)
    else:
        settings.ensure_data_layout()

    db_path = env.sqlite_db_path if env is not None else settings.db_path

    try:
        migration = run_migrations(db_path=db_path)
        gaps_before = sync_status_report(
            end_date, start=start_date, check_persist=True, db_path=db_path
        )
        should_sync = force or has_mandatory_gaps(gaps_before)
        invalidation: InvalidationRunResult | None = None
        ipca_dict_dates: list[str] | None = None
        if force and should_sync:
            scope, invalidation = run_pipeline_invalidation(
                datasets=datasets,
                start_date=start_date,
                end_date=end_date,
                refresh_dates=refresh_dates,
                db_path=db_path,
            )
            if scope is not None and scope.ipca_dict_calendar_days:
                ipca_dict_dates = list(scope.ipca_dict_calendar_days)
        sync_phases: tuple[SyncPhaseResult, ...] = ()
        if should_sync:
            phases = run_daily_sync(
                end_date,
                start_date=start_date,
                persist=persist,
                datasets=datasets,
                ipca_dict_dates=ipca_dict_dates,
            )
            sync_phases = tuple(phases)
        gaps_after = sync_status_report(
            end_date, start=start_date, check_persist=True, db_path=db_path
        )
        return UpdateDatabaseResult(
            data_root=env.data_root if env is not None else None,
            db_path=db_path,
            environment=env,
            migration=migration,
            gaps_before=gaps_before,
            gaps_after=gaps_after,
            sync_ran=should_sync,
            sync_phases=sync_phases,
            skipped_sync=not should_sync,
            invalidation=invalidation,
        )
    finally:
        settings.deactivate_path_overlay()
