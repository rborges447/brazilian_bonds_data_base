from __future__ import annotations

import pandas as pd

from rf_lake.gold.db.schema import AJUSTES_BMF_NUMERIC, AJUSTES_BMF_RENAME_MAP
from rf_lake.silver.normalize import normalize_date_columns, normalize_numeric_columns, remove_duplicate_columns
from rf_lake.bronze.sources.uptodata.mapping import filtro_DI_DAP


def normalize(df_raw: pd.DataFrame, dates: list[str] | None = None) -> pd.DataFrame:
    """
    AJUSTES_BMF-specific normalization (pipeline/notebook baseline).

    - Filter to DI/DAP when `TckrSymb` exists
    - Remove duplicate columns
    - Rename via `AJUSTES_BMF_RENAME_MAP`
    - Normalize pt-BR numerics (comma decimal)
    - Normalize dates to ISO
    - (Optional) filter `data_referencia` to `dates`
    """
    df = df_raw.copy()

    # DI/DAP filter (before rename: uses `TckrSymb`)
    if "TckrSymb" in df.columns:
        df = filtro_DI_DAP(df)

    # Remove duplicate columns before rename
    df = remove_duplicate_columns(df)

    # If both data_referencia and RptDt exist, drop RptDt before rename
    if "data_referencia" in df.columns and "RptDt" in df.columns:
        df = df.drop(columns=["RptDt"])

    # Rename columns (only those present)
    rename_map = {k: v for k, v in AJUSTES_BMF_RENAME_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Remove duplicate columns after rename
    df = remove_duplicate_columns(df)

    df = normalize_numeric_columns(df, AJUSTES_BMF_NUMERIC, use_comma_decimal=True)
    df = normalize_date_columns(df, ["data_referencia", "data_vencimento"])

    if dates is not None and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(dates))].copy()

    return df

