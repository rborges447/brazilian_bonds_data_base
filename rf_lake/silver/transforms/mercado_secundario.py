from __future__ import annotations

import pandas as pd

from rf_lake.gold.db.schema import MERCADO_SECUNDARIO_NUMERIC, MERCADO_SECUNDARIO_RENAME_MAP
from rf_lake.silver.normalize import normalize_date_columns, normalize_numeric_columns


def normalize(df_raw: pd.DataFrame, dates: list[str] | None = None) -> pd.DataFrame:
    """
    MERCADO_SECUNDARIO-specific normalization (pipeline baseline).

    - Rename columns via `MERCADO_SECUNDARIO_RENAME_MAP`
    - Normalize numerics
    - Normalize dates to ISO
    - (Optional) filter `data_referencia` to `dates`
    """
    df = df_raw.copy()

    df = df.rename(columns=MERCADO_SECUNDARIO_RENAME_MAP)
    df = normalize_numeric_columns(df, MERCADO_SECUNDARIO_NUMERIC)
    df = normalize_date_columns(df, ["data_referencia", "data_vencimento"])

    if dates is not None and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(dates))].copy()

    return df
