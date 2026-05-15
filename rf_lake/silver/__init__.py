"""Camada Silver."""

from typing import TYPE_CHECKING

__all__ = ["run_silver", "run_silver_phase"]

if TYPE_CHECKING:
    from rf_lake.silver.pipeline import run_silver, run_silver_phase


def __getattr__(name: str):
    if name in __all__:
        from rf_lake.silver import pipeline

        return getattr(pipeline, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
