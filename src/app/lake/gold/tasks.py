"""Gold task resolution for daily / sync pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.lake.gold.contracts import BUILDER_NAMES, BuilderName, is_snapshot_only_builder
from app.lake.gold.incremental import candidates_for_builder, missing_materialize_dates


@dataclass
class GoldTask:
    name: BuilderName
    dates: list[str] = field(default_factory=list)


def resolve_gold_tasks(
    target_date: str | None = None,
    *,
    start_date: str | None = None,
    persist: bool = False,
    builder: BuilderName | None = None,
) -> list[GoldTask]:
    """
    Build gold tasks for the canonical sync window.

    ``feriados`` is always included (snapshot refresh). Other builders receive
    only dates still missing materialization (silver-ready, optionally not in SQL).
    """
    from app.core.sync_range import sync_end_date, sync_start_date

    end = sync_end_date(target_date)
    start = sync_start_date(start_date)
    names: tuple[BuilderName, ...]
    if builder is not None:
        names = (builder,)
    else:
        names = tuple(n for n in BUILDER_NAMES if n != "vna_lft")

    tasks: list[GoldTask] = []
    for name in names:
        if is_snapshot_only_builder(name):
            tasks.append(GoldTask(name=name, dates=[]))
            continue
        candidates = candidates_for_builder(name, end, start=start)
        dates = missing_materialize_dates(
            name, candidates, persist=persist
        )
        if dates or name == "feriados":
            tasks.append(GoldTask(name=name, dates=dates))
    return tasks


__all__ = ["GoldTask", "resolve_gold_tasks"]
