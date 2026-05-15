"""Backfill em intervalo: orquestra Bronze → Silver → Gold em três fases."""

from __future__ import annotations

from datetime import date, timedelta

from rf_lake.bootstrap import bootstrap
from rf_lake.bronze import run_bronze_phase
from rf_lake.datasets import DATASETS, DatasetTask
from rf_lake.gold import run_gold_phase
from rf_lake.jobs.run_daily import _merge_phase_results
from rf_lake.logging import get_logger, setup_logging
from rf_lake.pipeline import run_dataset
from rf_lake.silver import run_silver_phase

setup_logging()
logger = get_logger(__name__)


def list_dates(start_date: str, end_date: str, skip_weekends: bool = True) -> list[str]:
    start_dt = date.fromisoformat(start_date)
    end_dt = date.fromisoformat(end_date)
    if start_dt > end_dt:
        return []
    out: list[str] = []
    cur = start_dt
    while cur <= end_dt:
        if (not skip_weekends) or (cur.weekday() < 5):
            out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def _resolve_backfill_tasks(start_date: str, end_date: str) -> list[DatasetTask]:
    dates = list_dates(start_date, end_date, skip_weekends=True)
    tasks: list[DatasetTask] = []
    for cfg in DATASETS.values():
        if cfg.date_mode == "missing_dates":
            task_dates = dates
        elif cfg.name == "projecoes":
            task_dates = [end_date]
        else:
            task_dates = []
        tasks.append(DatasetTask(name=cfg.name, dates=task_dates, config=cfg))
    return tasks


def backfill(start_date: str, end_date: str, pipeline: str | None = None) -> dict:
    bootstrap()

    if pipeline:
        dates = list_dates(start_date, end_date, skip_weekends=True)
        cfg = DATASETS.get(pipeline)
        if cfg is None:
            raise ValueError(f"Pipeline desconhecido: {pipeline}")
        if cfg.date_mode == "run_always" and pipeline in ("feriados", "ipca_indice"):
            dates = []
        elif cfg.date_mode == "run_always" and pipeline == "projecoes":
            dates = [end_date]
        return {pipeline: run_dataset(pipeline, dates, end_date=end_date)}

    tasks = _resolve_backfill_tasks(start_date, end_date)
    logger.info("Backfill %s .. %s (%s datasets)", start_date, end_date, len(tasks))

    bronze = run_bronze_phase(tasks)
    silver = run_silver_phase(tasks, bronze)
    gold = run_gold_phase(tasks, silver, end_date)

    return _merge_phase_results(tasks, bronze, silver, gold)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python -m rf_lake.jobs.backfill START_DATE END_DATE [PIPELINE]")
        sys.exit(1)
    start, end = sys.argv[1], sys.argv[2]
    pl = sys.argv[3] if len(sys.argv) > 3 else None
    print(backfill(start, end, pl))
