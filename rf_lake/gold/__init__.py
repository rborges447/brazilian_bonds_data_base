"""Camada Gold (persistência SQLite)."""

from typing import TYPE_CHECKING

__all__ = ["run_gold", "run_gold_phase"]

if TYPE_CHECKING:
    from rf_lake.gold.pipeline import run_gold, run_gold_phase


def __getattr__(name: str):
    if name in __all__:
        from rf_lake.gold import pipeline

        return getattr(pipeline, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
