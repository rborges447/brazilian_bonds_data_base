#!/usr/bin/env python
"""CLI for gold materialization and optional SQL persistence."""

from __future__ import annotations

import logging
import sys

import pandas as pd

from app.config import get_settings
from app.core.sync_range import sync_end_date, sync_start_date
from app.lake.gold.tasks import resolve_gold_tasks
from app.database import apply_migrations
from app.lake.gold import BUILDER_NAMES, GoldOrchestrator
from app.lake.gold.contracts import (
    BuilderContext,
    BuilderName,
    GoldMaterialized,
    is_snapshot_only_builder,
)
from app.services.gold_persistence import persist_materialized


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


def _print_materialized(result: GoldMaterialized, *, persisted: int | None = None) -> None:
    value = result.value
    if isinstance(value, pd.DataFrame):
        print(f"{result.name}: rows={len(value)} columns={len(value.columns)}")
        if not value.empty and "data_referencia" in value.columns:
            print(
                f"  range: {value['data_referencia'].min()} .. "
                f"{value['data_referencia'].max()}"
            )
    elif isinstance(value, list):
        print(f"{result.name}: items={len(value)}")
    else:
        print(f"{result.name}: type={type(value).__name__}")
    if persisted is not None:
        print(f"  persisted_rows={persisted}")


def _materialize_builder(
    orch: GoldOrchestrator,
    name: BuilderName,
    dates: list[str],
) -> GoldMaterialized:
    if name == "feriados":
        return orch.materialize_feriados()
    if name == "ipca_dict":
        return orch.materialize_ipca_dict(dates)
    if name == "cdi":
        return orch.materialize_cdi(dates)
    if name == "ptax":
        return orch.materialize_ptax(dates)
    if name == "bmf":
        return orch.materialize_bmf(dates)
    if name == "mercado_secundario":
        return orch.materialize_mercado_secundario(dates)
    if name == "liquidacoes_mercado":
        return orch.materialize_liquidacoes_mercado(dates)
    if name == "leiloes":
        return orch.materialize_leiloes(dates)
    if name == "vna":
        return orch.materialize_vna(dates)
    ctx = BuilderContext(dates=dates or None)
    return orch.materialize(name, ctx=ctx)


def _run_result(result: GoldMaterialized, *, do_persist: bool) -> None:
    persisted: int | None = None
    if do_persist:
        persisted = persist_materialized(result)
    _print_materialized(result, persisted=persisted)


def cmd_init() -> None:
    get_settings().ensure_data_layout()
    settings = get_settings()
    print("Data layout ready:")
    print("  DATA_ROOT:", settings.data_root)
    print("  SQLITE:", settings.db_path)


def cmd_migrate() -> None:
    apply_migrations()
    print("Migrations applied (schema v2).")


def cmd_one(builder: str, target: str | None, *, do_persist: bool) -> None:
    name: BuilderName = builder  # type: ignore[assignment]
    if name not in BUILDER_NAMES:
        print(f"Unknown builder: {builder}. Allowed: {list(BUILDER_NAMES)}")
        sys.exit(1)

    orch = GoldOrchestrator()
    if is_snapshot_only_builder(name):
        result = _materialize_builder(orch, name, [])
    elif target:
        result = _materialize_builder(orch, name, [target])
    else:
        print(f"Builder {name} requires a date argument.")
        sys.exit(1)
    _run_result(result, do_persist=do_persist)


def cmd_daily(target: str | None, *, do_persist: bool) -> None:
    tasks = resolve_gold_tasks(target, persist=do_persist)
    orch = GoldOrchestrator()
    for task in tasks:
        if not task.dates and task.name != "feriados":
            print(f"{task.name}: skip (nothing to materialize)")
            continue
        result = _materialize_builder(orch, task.name, task.dates)
        _run_result(result, do_persist=do_persist)


def cmd_catchup(*, do_persist: bool) -> None:
    """Backfill gold from DATA_START_DATE through today (missing only)."""
    cmd_daily(None, do_persist=do_persist)


def cmd_backfill(
    start: str, end: str, builder: str | None, *, do_persist: bool
) -> None:
    start = sync_start_date(start)
    end = sync_end_date(end)
    b: BuilderName | None = None
    if builder:
        if builder not in BUILDER_NAMES:
            print(f"Unknown builder: {builder}. Allowed: {list(BUILDER_NAMES)}")
            sys.exit(1)
        b = builder  # type: ignore[assignment]

    tasks = resolve_gold_tasks(end, start_date=start, persist=do_persist, builder=b)
    orch = GoldOrchestrator()
    for task in tasks:
        if not task.dates and task.name != "feriados":
            print(f"{task.name}: skip (nothing to materialize)")
            continue
        result = _materialize_builder(orch, task.name, task.dates)
        _run_result(result, do_persist=do_persist)


def main(argv: list[str] | None = None) -> None:
    _setup_logging()
    raw = argv if argv is not None else sys.argv[1:]
    args, do_persist = _consume_persist_flag(list(raw))

    if not args:
        print(
            "Usage:\n"
            "  python run_gold.py init\n"
            "  python run_gold.py migrate\n"
            "  python run_gold.py one BUILDER [YYYY-MM-DD] [--persist]\n"
            "  python run_gold.py daily [YYYY-MM-DD] [--persist]\n"
            "  python run_gold.py catchup [--persist]\n"
            "  python run_gold.py backfill START END [BUILDER] [--persist]\n"
            f"Builders: {list(BUILDER_NAMES)}"
        )
        sys.exit(1)

    cmd = args[0].lower()

    if cmd == "init":
        cmd_init()
        return

    if cmd == "migrate":
        cmd_migrate()
        return

    if cmd == "one":
        if len(args) < 2:
            print(
                f"Usage: python run_gold.py one BUILDER [DATE] [--persist]\n"
                f"Allowed: {list(BUILDER_NAMES)}"
            )
            sys.exit(1)
        target = args[2] if len(args) > 2 else None
        cmd_one(args[1], target, do_persist=do_persist)
        return

    if cmd == "daily":
        target = args[1] if len(args) > 1 else None
        cmd_daily(target, do_persist=do_persist)
        return

    if cmd == "catchup":
        cmd_catchup(do_persist=do_persist)
        return

    if cmd == "backfill":
        if len(args) < 3:
            print("Usage: python run_gold.py backfill START END [BUILDER] [--persist]")
            sys.exit(1)
        builder = args[3] if len(args) > 3 else None
        cmd_backfill(args[1], args[2], builder, do_persist=do_persist)
        return

    print(f"Unknown command: {cmd}")
    sys.exit(1)


if __name__ == "__main__":
    main()
