"""CDI: silver partitions → DataFrame ready for SQL INSERT."""

from __future__ import annotations

import pandas as pd

from pipelines.gold.contracts import BuilderContext, CdiGoldValue, SilverFrames

_DATASET = "cdi"
_COLS = ("data_referencia", "cdi")
_EMPTY = pd.DataFrame(columns=list(_COLS))


def from_silver(silver: SilverFrames, ctx: BuilderContext) -> CdiGoldValue:
    """
    Filter silver CDI to ``ctx.dates`` and return rows for SQL insert.

    Caller supplies ``dates`` (ISO YYYY-MM-DD); no transform beyond normalize/sort.
    """
    if ctx.dates is None:
        raise ValueError("CDI materialization requires ctx.dates (list of ISO dates).")
    if not ctx.dates:
        return _EMPTY.copy()

    if _DATASET not in silver:
        raise KeyError(
            f"Silver dataset '{_DATASET}' missing. Run bronze/silver for cdi first."
        )
    df = silver[_DATASET]
    if df is None or df.empty:
        raise ValueError(
            f"Silver cdi is empty for requested dates: {ctx.dates}. "
            "Run bronze/silver for those partitions."
        )
    for col in _COLS:
        if col not in df.columns:
            raise ValueError(f"Silver cdi must have column '{col}', got: {list(df.columns)}")

    requested = {d.strip()[:10] for d in ctx.dates}
    out = df.copy()
    out["data_referencia"] = out["data_referencia"].astype(str).str.strip().str[:10]
    out = out[out["data_referencia"].isin(requested)]
    out = out[list(_COLS)].drop_duplicates(subset=["data_referencia"]).sort_values(
        "data_referencia"
    )
    out = out.reset_index(drop=True)

    found = set(out["data_referencia"])
    missing = sorted(requested - found)
    if missing:
        raise ValueError(
            f"Silver cdi has no rows for requested dates: {missing}. "
            f"Loaded {len(df)} row(s) from silver."
        )
    return out
