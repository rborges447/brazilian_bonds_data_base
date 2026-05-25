"""
Shared helpers for gold builders (phase B).

Each builder implements ``build(silver, ctx) -> gold_ready`` and is wired in ``registry.build``.
"""

from __future__ import annotations

import pandas as pd

from app.lake.gold.contracts import BuilderContext, SilverFrames


def resolve_as_of_date(ctx: BuilderContext) -> pd.Timestamp:
    """Default reference date: today normalized (business-day logic in phase B)."""
    if ctx.as_of_date is not None:
        return pd.Timestamp(ctx.as_of_date).normalize()
    return pd.Timestamp.today().normalize()


def require_dataset(silver: SilverFrames, dataset: str) -> pd.DataFrame:
    """Return a non-empty silver frame or raise."""
    if dataset not in silver:
        raise KeyError(f"Silver dataset missing: {dataset}")
    df = silver[dataset]
    if df is None or df.empty:
        raise ValueError(f"Silver dataset empty: {dataset}. Run silver pipeline first.")
    return df
