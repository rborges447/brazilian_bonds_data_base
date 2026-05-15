"""
Daily job: orchestrates Bronze → Silver → Gold in three phases.
"""

from __future__ import annotations

from datetime import date

from rf_lake.bootstrap import bootstrap
from rf_lake.bronze import run_bronze_phase
from rf_lake.datasets import DATASETS, resolve_tasks
from rf_lake.gold import run_gold_phase
from rf_lake.gold.db.queries import get_max_date
from rf_lake.logging import get_logger, setup_logging
from rf_lake.silver import run_silver_phase
from rf_lake.watermarks import get_watermark

setup_logging()
logger = get_logger(__name__)


def _merge_phase_results(tasks, bronze, silver, gold) -> dict:
    out: dict = {}
    for task in tasks:
        b = bronze.get(task.name)
        s = silver.get(task.name)
        g = gold.get(task.name)

        all_skipped = (
            b and b.status == "skipped"
            and s and s.status == "skipped"
            and g and g.status == "skipped"
        )
        any_error = (
            (b and b.status == "error")
            or (s and s.status == "error")
            or (g and g.status == "error")
        )

        if any_error:
            status = "error"
        elif all_skipped and not task.dates:
            status = "skipped"
        elif all_skipped:
            status = "skipped"
        elif g and g.persisted:
            status = "success"
        elif g and g.status == "skipped" and not task.dates:
            status = "skipped"
        else:
            status = "failed"

        cfg = task.config or DATASETS.get(task.name)
        gold_max = None
        if cfg and cfg.table and cfg.date_col:
            gold_max = get_max_date(cfg.table, cfg.date_col)

        out[task.name] = {
            "status": status,
            "reason": "no_missing_dates" if all_skipped and not any_error else None,
            "dates_candidate": task.dates,
            "bronze_last_date": get_watermark(task.name, "bronze"),
            "silver_last_date": get_watermark(task.name, "silver"),
            "gold_max_date": gold_max,
            "bronze": {
                "status": b.status if b else None,
                "raw_rows": b.raw_rows if b else 0,
                "dates_processed": b.dates_processed if b else [],
            },
            "silver": {
                "status": s.status if s else None,
                "transformed_rows": s.rows if s else 0,
                "dates_processed": s.dates_processed if s else [],
            },
            "gold": {
                "status": g.status if g else None,
                "persisted": g.persisted if g else False,
                "rows": g.rows if g else 0,
                "dates_loaded": g.dates_loaded if g else [],
            },
            "raw_rows": b.raw_rows if b else 0,
            "transformed_rows": s.rows if s else 0,
            "persisted": g.persisted if g else False,
        }
    return out


def run_daily(target_date: str | None = None) -> dict:
    bootstrap()

    if target_date is None:
        target_date = date.today().isoformat()

    logger.info("rf_lake daily job for %s", target_date)
    tasks = resolve_tasks(target_date)

    bronze = run_bronze_phase(tasks)
    silver = run_silver_phase(tasks, bronze)
    gold = run_gold_phase(tasks, silver, target_date)

    results = _merge_phase_results(tasks, bronze, silver, gold)
    logger.info("Daily job completed.")
    return results


if __name__ == "__main__":
    run_daily()
