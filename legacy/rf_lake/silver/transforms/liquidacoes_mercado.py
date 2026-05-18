from __future__ import annotations

import pandas as pd

from rf_lake.gold.db.schema import LIQUIDACOES_MERCADO_NUMERIC, LIQUIDACOES_MERCADO_RENAME_MAP
from rf_lake.silver.normalize import normalize_date_columns, normalize_numeric_columns


def normalize(df_raw: pd.DataFrame, dates: list[str] | None = None) -> pd.DataFrame:
    """
    LIQUIDACOES_MERCADO-specific normalization (pipeline baseline).

    - Rename columns via `LIQUIDACOES_MERCADO_RENAME_MAP`
    - Normalize pt-BR numerics (comma decimal)
    - Normalize dates to ISO
    - (Optional) filter `data_referencia` to `dates` (guard rail for DATA MOV)
    """
    df = df_raw.copy()

    df = df.rename(columns=LIQUIDACOES_MERCADO_RENAME_MAP)
    df = normalize_numeric_columns(df, LIQUIDACOES_MERCADO_NUMERIC, use_comma_decimal=True)
    df = normalize_date_columns(df, ["data_referencia", "data_vencimento"])

    if dates is not None and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(dates))].copy()

    return df

