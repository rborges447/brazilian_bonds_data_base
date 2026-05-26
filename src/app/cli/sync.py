#!/usr/bin/env python
"""Unified sync CLI: bronze → silver → gold over [DATA_START_DATE, end]."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from app.cli.bronze import _print_results as print_bronze_results
from app.cli.gold import _setup_logging as setup_gold_logging
from app.cli.silver import _print_results as print_silver_results
from app.config import get_settings
from app.core.sync_range import sync_end_date, sync_start_date
from app.core.sync_verify import has_mandatory_gaps, sync_status_report
from app.services.pipeline_invalidation import InvalidationRunResult
from app.services.sync_runner import SyncPhaseResult, run_daily_sync
from app.services.update_database_service import UpdateDatabaseResult, update_database


def _setup_logging() -> None:
    level_name = get_settings().log_level
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


@dataclass(frozen=True)
class DailyOptions:
    end_date: str | None
    do_persist: bool
    force: bool
    start_date: str | None
    datasets: list[str] | None
    refresh_dates: list[str] | None


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_daily_args(argv: list[str]) -> DailyOptions:
    """Parse ``daily`` positional end date and optional flags."""
    end_date: str | None = None
    do_persist = False
    force = False
    start_date: str | None = None
    datasets: list[str] | None = None
    refresh_dates: list[str] | None = None

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--persist":
            do_persist = True
        elif arg == "--force":
            force = True
        elif arg == "--start-date":
            i += 1
            if i >= len(argv):
                raise ValueError("--start-date requires a value")
            start_date = argv[i]
        elif arg == "--datasets":
            i += 1
            if i >= len(argv):
                raise ValueError("--datasets requires a value")
            datasets = _split_csv(argv[i])
        elif arg == "--refresh-dates":
            i += 1
            if i >= len(argv):
                raise ValueError("--refresh-dates requires a value")
            refresh_dates = _split_csv(argv[i])
        elif not arg.startswith("-") and end_date is None:
            end_date = arg
        else:
            raise ValueError(f"Unknown or duplicate argument: {arg}")
        i += 1

    if refresh_dates and not force:
        print(
            "Warning: --refresh-dates ignored without --force",
            file=sys.stderr,
        )
        refresh_dates = None

    return DailyOptions(
        end_date=end_date,
        do_persist=do_persist,
        force=force,
        start_date=start_date,
        datasets=datasets,
        refresh_dates=refresh_dates,
    )


def _print_invalidation_summary(invalidation: InvalidationRunResult | None) -> None:
    if invalidation is None:
        return
    print("=== Invalidation ===")
    print(f"  bronze files removed: {invalidation.bronze_files_removed}")
    print(f"  silver files removed: {invalidation.silver_files_removed}")
    print(f"  gold rows deleted: {invalidation.gold_rows_deleted}")


def _print_sync_phases(phases: tuple[SyncPhaseResult, ...]) -> None:
    if not phases:
        return
    print("=== Bronze ===")
    print_bronze_results(phases[0].details)
    print("=== Silver ===")
    print_silver_results(phases[1].details)
    print("=== Gold ===")
    setup_gold_logging()
    print(f"gold: {phases[2].task_count} task(s)")


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


def cmd_daily(options: DailyOptions) -> int:
    if options.force:
        result = update_database(
            force=True,
            persist=options.do_persist,
            start_date=options.start_date,
            end_date=options.end_date,
            datasets=options.datasets,
            refresh_dates=options.refresh_dates,
        )
        _print_invalidation_summary(result.invalidation)
        _print_sync_phases(result.sync_phases)
        print("=== Status ===")
        return cmd_status(options.end_date, check_persist=True)

    print("=== Bronze ===")
    phases = run_daily_sync(options.end_date, persist=options.do_persist)
    print_bronze_results(phases[0].details)
    print("=== Silver ===")
    print_silver_results(phases[1].details)
    print("=== Gold ===")
    setup_gold_logging()
    print(f"gold: {phases[2].task_count} task(s)")
    print("=== Status ===")
    return cmd_status(options.end_date, check_persist=True)


def _usage() -> str:
    return (
        "Usage:\n"
        "  python run_sync.py daily [YYYY-MM-DD] [--persist] [--force]\n"
        "      [--start-date YYYY-MM-DD] [--datasets NAME,...]\n"
        "      [--refresh-dates YYYY-MM-DD,...]\n"
        "  python run_sync.py status [YYYY-MM-DD]"
    )


def main(argv: list[str] | None = None) -> None:
    _setup_logging()
    raw = argv if argv is not None else sys.argv[1:]

    if not raw:
        print(_usage())
        sys.exit(1)

    cmd = raw[0].lower()
    rest = raw[1:]

    if cmd == "status":
        end = rest[0] if rest and not rest[0].startswith("-") else None
        code = cmd_status(end, check_persist=True)
        sys.exit(code)

    if cmd == "daily":
        try:
            options = _parse_daily_args(rest)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            print(_usage(), file=sys.stderr)
            sys.exit(2)
        code = cmd_daily(options)
        sys.exit(code)

    print(f"Unknown command: {cmd}")
    sys.exit(1)


if __name__ == "__main__":
    main()
