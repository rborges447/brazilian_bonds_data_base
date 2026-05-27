"""VNA: silver partitions → DataFrame ready for SQL INSERT."""

from __future__ import annotations

import pandas as pd

from app.lake.gold.contracts import BuilderContext, SilverFrames, VnaGoldValue
from app.lake.gold.materializers._tabular import (
    prepare_tabular_output,
    raise_if_missing_enforced_dates,
    resolve_enforce_dates,
)

_DATASET = "vna"
_REQUIRED_SILVER = (
    "data_referencia",
    "codigo_selic",
    "tipo_correcao",
    "index",
    "data_validade",
    "vna",
)
_OUTPUT_COLS = (*_REQUIRED_SILVER, "vna_ajustado")
_DEDUP_SUBSET = ("data_referencia", "codigo_selic")
_SORT_BY = ("data_referencia", "codigo_selic")
_EMPTY = pd.DataFrame(columns=list(_OUTPUT_COLS))


def from_silver(silver: SilverFrames, ctx: BuilderContext) -> VnaGoldValue:
    """
    Filter silver VNA to ``ctx.dates`` and return rows for SQL insert.

    ``vna_ajustado`` is filled with NULL at gold when absent in silver.
    """
    if ctx.dates is None:
        raise ValueError("VNA materialization requires ctx.dates (list of ISO dates).")
    if not ctx.dates:
        return _EMPTY.copy()

    if _DATASET not in silver:
        raise KeyError(
            f"Silver dataset '{_DATASET}' missing. Run bronze/silver for vna first."
        )
    df = silver[_DATASET]
    requested = {d.strip()[:10] for d in ctx.dates}
    enforce_dates, skipped_partitions = resolve_enforce_dates(ctx, _DATASET, requested)

    if not enforce_dates:
        return _EMPTY.copy()
    if df is None or df.empty:
        raise ValueError(
            f"Silver vna is empty for loaded partitions: {sorted(enforce_dates)}. "
            "Run bronze/silver for those partitions."
        )

    out = df.copy()
    out["data_referencia"] = out["data_referencia"].astype(str).str.strip().str[:10]
    out = out[out["data_referencia"].isin(requested)]
    out = prepare_tabular_output(
        out,
        dataset=_DATASET,
        required_silver=_REQUIRED_SILVER,
        output_columns=_OUTPUT_COLS,
    )
    out["codigo_selic"] = pd.to_numeric(out["codigo_selic"], errors="coerce").astype("Int64")
    out = (
        out.drop_duplicates(subset=list(_DEDUP_SUBSET), keep="last")
        .sort_values(list(_SORT_BY))
        .reset_index(drop=True)
    )

    found_dates = set(out["data_referencia"].astype(str).str.strip().str[:10])
    raise_if_missing_enforced_dates(
        dataset=_DATASET,
        enforce_dates=enforce_dates,
        found_dates=found_dates,
        loaded_row_count=len(df),
        skipped_partitions=skipped_partitions,
    )
    return out
