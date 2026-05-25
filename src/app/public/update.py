"""Public update entrypoint (facade over internal sync/migration)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.update_database_service import UpdateDatabaseResult, update_database


def update(
    *,
    data_root: str | Path | None = None,
    datasets: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    force: bool = False,
    persist: bool = True,
    **kwargs: Any,
) -> UpdateDatabaseResult:
    """Refresh local database content (migrations + optional bronze/silver/gold sync)."""
    if kwargs:
        raise TypeError(f"unexpected keyword arguments: {sorted(kwargs)}")
    return update_database(
        data_root=data_root,
        datasets=datasets,
        start_date=start_date,
        end_date=end_date,
        force=force,
        persist=persist,
    )
