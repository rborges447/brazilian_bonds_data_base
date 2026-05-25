#!/usr/bin/env python
"""Unified sync CLI: bronze → silver → gold over [DATA_START_DATE, end]."""

from __future__ import annotations

import logging
import sys

from app.cli.bronze import _print_results as print_bronze_results
from app.cli.gold import _materialize_builder, _run_result, _setup_logging as setup_gold_logging
from app.cli.silver import _print_results as print_silver_results
from app.config import get_settings
from app.core.sync_range import sync_end_date, sync_start_date
from app.core.sync_verify import has_mandatory_gaps, sync_status_report
from app.lake.bronze.pipeline import run_bronze_phase
from app.lake.bronze.tasks import resolve_bronze_tasks
from app.lake.gold import GoldOrchestrator
from app.lake.gold.tasks import resolve_gold_tasks
from app.lake.silver.pipeline import run_silver_phase
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


def _consume_persist_flag(argv: list[str]) -> tuple[list[str], bool]:
    persist = "--persist" in argv
    if persist:
        argv = [a for a in argv if a != "--persist"]
    return argv, persist


def cmd_status(end: str | None, *, check_persist: bool = True) -> int:
    report = sync_status_report(end, check_persist=check_persist)
    range_start = sync_start_date()
    range_end = sync_end_date(end)
    print(f"Sync coverage [{range_start} .. {range_end}]")
    for layer, gaps in report.items():
        if not gaps:
            print(f"  {layer}: OK")
            continue
        print(f"  {layer}:")
        for name, values in sorted(gaps.items()):
            preview = values[:5]
            suffix = f" ... +{len(values) - 5}" if len(values) > 5 else ""
            print(f"    {name}: {len(values)} gap(s) {preview}{suffix}")
    return 1 if has_mandatory_gaps(report) else 0


def cmd_daily(end: str | None, *, do_persist: bool) -> int:
    get_settings().ensure_data_layout()

    print("=== Bronze ===")
    bronze_tasks = resolve_bronze_tasks(end)
    bronze_results = run_bronze_phase(bronze_tasks)
    print_bronze_results(bronze_results)

    print("=== Silver ===")
    silver_tasks = resolve_silver_tasks(end)
    silver_results = run_silver_phase(silver_tasks)
    print_silver_results(silver_results)

    print("=== Gold ===")
    setup_gold_logging()
    gold_tasks = resolve_gold_tasks(end, persist=do_persist)
    orch = GoldOrchestrator()
    for task in gold_tasks:
        if not task.dates and task.name != "feriados":
            print(f"{task.name}: skip (nothing to materialize)")
            continue
        result = _materialize_builder(orch, task.name, task.dates)
        _run_result(result, do_persist=do_persist)

    print("=== Status ===")
    return cmd_status(end, check_persist=True)


def main(argv: list[str] | None = None) -> None:
    _setup_logging()
    raw = argv if argv is not None else sys.argv[1:]
    args, do_persist = _consume_persist_flag(list(raw))

    if not args:
        print(
            "Usage:\n"
            "  python run_sync.py daily [YYYY-MM-DD] [--persist]\n"
            "  python run_sync.py status [YYYY-MM-DD]"
        )
        sys.exit(1)

    cmd = args[0].lower()
    end = args[1] if len(args) > 1 and not args[1].startswith("-") else None

    if cmd == "status":
        # Status always checks SQLite gaps; --persist applies only to ``daily``.
        code = cmd_status(end, check_persist=True)
        sys.exit(code)

    if cmd == "daily":
        code = cmd_daily(end, do_persist=do_persist)
        sys.exit(code)

    print(f"Unknown command: {cmd}")
    sys.exit(1)


if __name__ == "__main__":
    main()
