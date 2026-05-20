"""BMF ajustes: silver partitions → DataFrame ready for SQL INSERT."""

from __future__ import annotations

import pandas as pd

from pipelines.gold.contracts import BmfGoldValue, BuilderContext, SilverFrames

_DATASET = "ajustes_bmf"
_COLS = (
    "data_referencia",
    "data_vencimento",
    "ticker",
    "taxa_ajuste",
    "quantidade_ajuste",
    "codigo_isin",
)
_EMPTY = pd.DataFrame(columns=list(_COLS))
_DEDUP_SUBSET = ("data_referencia", "ticker")
_SORT_BY = ("data_referencia", "data_vencimento", "ticker")


def from_silver(silver: SilverFrames, ctx: BuilderContext) -> BmfGoldValue:
    """
    Filter silver ajustes_bmf to ``ctx.dates`` and return rows for SQL insert.

    Caller supplies ``dates`` (ISO YYYY-MM-DD); no transform beyond normalize/sort.
    """
    if ctx.dates is None:
        raise ValueError("BMF materialization requires ctx.dates (list of ISO dates).")
    if not ctx.dates:
        return _EMPTY.copy()

    if _DATASET not in silver:
        raise KeyError(
            f"Silver dataset '{_DATASET}' missing. Run bronze/silver for ajustes_bmf first."
        )
    df = silver[_DATASET]
    if df is None or df.empty:
        raise ValueError(
            f"Silver ajustes_bmf is empty for requested dates: {ctx.dates}. "
            "Run bronze/silver for those partitions."
        )
    for col in _COLS:
        if col not in df.columns:
            raise ValueError(
                f"Silver ajustes_bmf must have column '{col}', got: {list(df.columns)}"
            )

    requested = {d.strip()[:10] for d in ctx.dates}
    out = df.copy()
    out["data_referencia"] = out["data_referencia"].astype(str).str.strip().str[:10]
    out = out[out["data_referencia"].isin(requested)]
    out = (
        out[list(_COLS)]
        .drop_duplicates(subset=list(_DEDUP_SUBSET))
        .sort_values(list(_SORT_BY))
        .reset_index(drop=True)
    )

    found_dates = set(out["data_referencia"])
    missing_dates = sorted(requested - found_dates)
    if missing_dates:
        raise ValueError(
            f"Silver ajustes_bmf has no rows for requested dates: {missing_dates}. "
            f"Loaded {len(df)} row(s) from silver."
        )
    return out
