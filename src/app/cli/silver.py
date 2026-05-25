#!/usr/bin/env python
"""CLI for the hive-partitioned silver layer."""

from __future__ import annotations

import logging
import sys
from datetime import date

from app.config import get_settings
from app.core.dates import months_in_range
from app.core.sync_range import sync_end_date, sync_start_date
from app.core.datasets import get_dataset_config
from app.core.partitioning import PIPELINE_NAMES, is_snapshot_dataset
from app.lake.silver.pipeline import run_silver, run_silver_phase
from app.lake.silver.tasks import resolve_silver_tasks


def _setup_logging() -> None:
    level_name = get_settings().log_level
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def _print_results(results: dict) -> None:
    for name, result in results.items():
        print(
            f"{name}: {result.status} "
            f"rows={result.row_count} "
            f"partitions={result.segment_keys} "
            f"path={result.path}"
        )
        if result.error:
            print(f"  error: {result.error}")


def cmd_init() -> None:
    get_settings().ensure_data_layout()
    settings = get_settings()
    print("Data layout ready:")
    print("  DATA_ROOT:", settings.data_root)
    print("  BRONZE:", settings.bronze_root)
    print("  SILVER:", settings.silver_root)


def cmd_daily(target: str | None) -> None:
    tasks = resolve_silver_tasks(target)
    results = run_silver_phase(tasks)
    _print_results(results)


def cmd_one(pipeline: str, target: str | None) -> None:
    get_dataset_config(pipeline)
    settings = get_settings()
    target_date = sync_end_date(target)
    range_start = sync_start_date()

    if is_snapshot_dataset(pipeline):
        dates: list[str] = []
    elif pipeline in ("ipca_indice", "projecoes"):
        dates = months_in_range(range_start, target_date)
    elif target:
        dates = [target]
    else:
        dates = [target_date]

    result = run_silver(pipeline, dates)
    _print_results({pipeline: result})


def _backfill_tasks(start: str, end: str, pipeline: str | None) -> list:
    tasks = resolve_silver_tasks(end, start_date=start)
    if pipeline:
        tasks = [t for t in tasks if t.name == pipeline]
    return tasks


def cmd_backfill(start: str, end: str, pipeline: str | None) -> None:
    start = sync_start_date(start)
    end = sync_end_date(end)
    tasks = _backfill_tasks(start, end, pipeline)
    if not tasks:
        print("No silver partitions to process.")
        return
    results = run_silver_phase(tasks)
    _print_results(results)


def main() -> None:
    _setup_logging()

    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python run_silver.py init\n"
            "  python run_silver.py daily [YYYY-MM-DD]\n"
            "  python run_silver.py one PIPELINE [YYYY-MM-DD]\n"
            "  python run_silver.py backfill START_DATE END_DATE [PIPELINE]"
        )
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "init":
        cmd_init()
        return

    if cmd == "daily":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_daily(target)
        return

    if cmd == "one":
        if len(sys.argv) < 3:
            print(f"Usage: python run_silver.py one PIPELINE [DATE]\nAllowed: {list(PIPELINE_NAMES)}")
            sys.exit(1)
        pipeline = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) > 3 else None
        if pipeline not in PIPELINE_NAMES:
            print(f"Unknown pipeline: {pipeline}. Allowed: {list(PIPELINE_NAMES)}")
            sys.exit(1)
        cmd_one(pipeline, target)
        return

    if cmd == "backfill":
        if len(sys.argv) < 4:
            print("Usage: python run_silver.py backfill START_DATE END_DATE [PIPELINE]")
            sys.exit(1)
        start, end = sys.argv[2], sys.argv[3]
        pipeline = sys.argv[4] if len(sys.argv) > 4 else None
        if pipeline and pipeline not in PIPELINE_NAMES:
            print(f"Unknown pipeline: {pipeline}. Allowed: {list(PIPELINE_NAMES)}")
            sys.exit(1)
        cmd_backfill(start, end, pipeline)
        return

    print(f"Unknown command: {cmd}")
    sys.exit(1)
