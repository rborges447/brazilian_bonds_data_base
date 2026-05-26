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
    refresh_dates: list[str] | None = None,
    **kwargs: Any,
) -> UpdateDatabaseResult:
    """Refresh local database content.

    This entrypoint runs migrations and, when needed, executes the bronze → silver →
    gold sync pipeline. The key feature for consumers is the semantics of
    ``force=True`` which performs a destructive refresh in the selected scope
    (bronze/silver/gold), then reprocesses the pipeline.

    Args:
        data_root: Optional root path for the package layout (create local data
            directories when missing).
        datasets: Optional list of dataset names to refresh. ``None`` means all
            registered datasets in the pipeline.
        start_date: Start of the sync/invalidation window (YYYY-MM-DD).
        end_date: End of the sync/invalidation window (YYYY-MM-DD).
        force: When ``False`` (default), behaves incrementally and only syncs where
            gaps require it. When ``True``, it deletes and reprocesses bronze,
            silver and gold within the scope (``datasets`` + the date window) before
            running sync.
        persist: When ``False``, runs the pipeline but does not persist results to
            storage.
        refresh_dates: Optional explicit ISO dates used to restrict the daily
            invalidation when ``force=True``. If omitted and ``force=True``, the
            invalidation covers the whole window.

    Returns:
        UpdateDatabaseResult: Includes sync metadata, gaps reports, and (when
        ``force=True``) optional invalidation counters.

    Notes:
        - ``read_data()`` is read-only; use ``update(force=True)`` + then
          ``read_data()`` to observe refreshed data.
        - ``ipca_dict`` has special behavior: invalidating an IPCA monthly partition
          implies rebuilding the daily ``IPCA_DICT`` series up to the end of the sync
          window (FR-009). This reuses the existing gold logic.
        - ``feriados`` is a snapshot dataset: when included in the scope, the gold
          ``FERIADOS`` table is replaced entirely.

    Examples:
        BMF/DAP motivator (single day):
            See README for a full runnable example.
    """
    if kwargs:
        raise TypeError(f"unexpected keyword arguments: {sorted(kwargs)}")
    return update_database(
        data_root=data_root,
        datasets=datasets,
        start_date=start_date,
        end_date=end_date,
        force=force,
        persist=persist,
        refresh_dates=refresh_dates,
    )
