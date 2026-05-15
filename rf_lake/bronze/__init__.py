"""Camada Bronze: extração e dados brutos."""

from typing import TYPE_CHECKING

__all__ = ["run_bronze", "run_bronze_phase"]

if TYPE_CHECKING:
    from rf_lake.bronze.pipeline import BronzeResult, run_bronze, run_bronze_phase


def __getattr__(name: str):
    if name in __all__:
        from rf_lake.bronze import pipeline

        return getattr(pipeline, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
