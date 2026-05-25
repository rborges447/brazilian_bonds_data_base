"""Orchestrate local environment, migrations, gap detection, and daily sync."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.sync_verify import has_mandatory_gaps, sync_status_report
from app.services.local_environment_service import LocalEnvironment, ensure_local_environment
from app.services.migration_service import MigrationRunResult, run_migrations
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


def update_database(
    *,
    data_root: str | Path | None = None,
    datasets: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    force: bool = False,
    persist: bool = True,
    base: Path | None = None,
) -> UpdateDatabaseResult:
    """Initialize storage, migrate schema, optionally run bronze/silver/gold sync."""
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
        sync_phases: tuple[SyncPhaseResult, ...] = ()
        if should_sync:
            phases = run_daily_sync(
                end_date, start_date=start_date, persist=persist, datasets=datasets
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
        )
    finally:
        settings.deactivate_path_overlay()
