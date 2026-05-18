"""rf_lake job entry points (lazy imports)."""

from typing import TYPE_CHECKING

__all__ = ["backfill", "run_daily", "run_one"]

if TYPE_CHECKING:
    from rf_lake.jobs.backfill import backfill
    from rf_lake.jobs.run_daily import run_daily
    from rf_lake.jobs.run_one import run_one


def __getattr__(name: str):
    if name == "backfill":
        from rf_lake.jobs.backfill import backfill

        return backfill
    if name == "run_daily":
        from rf_lake.jobs.run_daily import run_daily

        return run_daily
    if name == "run_one":
        from rf_lake.jobs.run_one import run_one

        return run_one
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
