"""Leilões: silver partitions → DataFrame ready for SQL INSERT (LEILOES)."""

from __future__ import annotations

import pandas as pd

from app.lake.gold.contracts import BuilderContext, LeiloesGoldValue, SilverFrames
from app.lake.gold.materializers._tabular import prepare_tabular_output

_DATASET = "leiloes"
_REQUIRED_SILVER = (
    "numero_edital",
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
)
_OPTIONAL_SILVER = (
    "oferta",
    "quantidade_aceita",
    "percentual_corte",
    "oferta_segunda_volta",
    "financeiro_aceito",
    "financeiro_aceito_segunda_volta",
    "quantidade_aceita_segunda_volta",
    "pu_medio",
    "taxa_media",
)
_OUTPUT_COLS = (*_REQUIRED_SILVER, *_OPTIONAL_SILVER)
_EMPTY = pd.DataFrame(columns=list(_OUTPUT_COLS))
_DEDUP_SUBSET = ("tipo_titulo", "data_vencimento", "data_referencia", "numero_edital")
_SORT_BY = ("data_referencia", "numero_edital", "tipo_titulo", "data_vencimento")


def from_silver(silver: SilverFrames, ctx: BuilderContext) -> LeiloesGoldValue:
    """
    Filter silver leiloes to ``ctx.dates`` and return rows for SQL insert into LEILOES.

    Dates without a silver partition are ignored (leilões are sparse by auction day).
    If no requested date has a partition, returns an empty DataFrame with gold columns.
    """
    if ctx.dates is None:
        raise ValueError(
            "Leiloes materialization requires ctx.dates (list of ISO dates)."
        )
    if not ctx.dates:
        return _EMPTY.copy()

    if _DATASET not in silver:
        raise KeyError(
            f"Silver dataset '{_DATASET}' missing. Run bronze/silver for leiloes first."
        )
    df = silver[_DATASET]
    requested = {d.strip()[:10] for d in ctx.dates}
    loaded_key = f"loaded_partitions_{_DATASET}"
    if loaded_key in ctx.extras:
        enforce_dates = set(ctx.extras[loaded_key])
        skipped_partitions = sorted(requested - enforce_dates)
    else:
        enforce_dates = requested
        skipped_partitions = []

    if not enforce_dates:
        return _EMPTY.copy()
    if df is None or df.empty:
        return _EMPTY.copy()

    out = df.copy()
    out["data_referencia"] = out["data_referencia"].astype(str).str.strip().str[:10]
    out = out[out["data_referencia"].isin(requested)]
    out = prepare_tabular_output(
        out,
        dataset=_DATASET,
        required_silver=_REQUIRED_SILVER,
        optional_silver=_OPTIONAL_SILVER,
    )
    out = (
        out.drop_duplicates(subset=list(_DEDUP_SUBSET))
        .sort_values(list(_SORT_BY))
        .reset_index(drop=True)
    )

    found_dates = set(out["data_referencia"].astype(str).str.strip().str[:10])
    missing_dates = sorted(enforce_dates - found_dates)
    if missing_dates:
        raise ValueError(
            f"Silver leiloes has no rows for requested dates: {missing_dates}. "
            f"Loaded {len(df)} row(s) from silver."
            + (
                f" (no partition for: {skipped_partitions})"
                if skipped_partitions
                else ""
            )
        )
    return out
