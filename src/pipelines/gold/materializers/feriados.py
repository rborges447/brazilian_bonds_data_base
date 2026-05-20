"""Feriados: silver snapshot → list of ISO dates for FERIADOS SQL."""

from __future__ import annotations

from pipelines.gold.contracts import BuilderContext, FeriadosGoldValue, SilverFrames

_DATASET = "feriados"
_COL = "data"


def from_silver(silver: SilverFrames, ctx: BuilderContext) -> FeriadosGoldValue:
    del ctx
    """
    Extract holiday dates from silver (column ``data``, YYYY-MM-DD).

    No business transform — pipeline decides when to persist to SQLite.
    """
    if _DATASET not in silver:
        raise KeyError(
            f"Silver dataset '{_DATASET}' missing. Run bronze/silver for feriados first."
        )
    df = silver[_DATASET]
    if df is None or df.empty:
        raise ValueError(
            "Silver feriados is empty. Run: python run_bronze.py one feriados && "
            "python run_silver.py one feriados"
        )
    if _COL not in df.columns:
        raise ValueError(f"Silver feriados must have column '{_COL}', got: {list(df.columns)}")

    series = df[_COL].astype(str).str.strip().str[:10]
    series = series[series.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
    if series.empty:
        raise ValueError("Silver feriados has no valid ISO dates in column 'data'.")

    return series.drop_duplicates().sort_values().tolist()
