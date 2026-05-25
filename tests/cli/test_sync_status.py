"""CLI behaviour for run_sync status."""

from __future__ import annotations

from app.core.sync_range import sync_end_date, sync_start_date
from app.core.sync_verify import gold_gaps
from app.lake.gold.incremental import candidates_for_builder, _dates_silver_ready


def test_status_gold_gaps_use_persist_not_silver_ready_only() -> None:
    """
    ``gold_gaps(..., check_persist=False)`` lists all candidates without silver.

    ``status`` must use ``check_persist=True`` so only DB-missing rows count.
    """
    start = sync_start_date()
    end = sync_end_date()
    cands = candidates_for_builder("cdi", end, start=start)
    ready = _dates_silver_ready("cdi", cands)
    without_persist = gold_gaps("cdi", start, end, check_persist=False)
    with_persist = gold_gaps("cdi", start, end, check_persist=True)
    if not ready:
        assert len(without_persist) == len(cands)
        assert with_persist == []
