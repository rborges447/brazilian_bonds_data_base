from __future__ import annotations

import pandas as pd

from app.lake.silver.normalize import normalize_date_columns, normalize_numeric_columns
from app.lake.silver.schemas import LIQUIDACOES_MERCADO_NUMERIC, LIQUIDACOES_MERCADO_RENAME_MAP


def normalize_partition(
    df_raw: pd.DataFrame,
    partition_value: str,
    dates: list[str] | None = None,
) -> pd.DataFrame:
    df = df_raw.copy()
    df = df.rename(columns=LIQUIDACOES_MERCADO_RENAME_MAP)
    df = normalize_numeric_columns(df, LIQUIDACOES_MERCADO_NUMERIC, use_comma_decimal=True)
    df = normalize_date_columns(df, ["data_referencia", "data_vencimento"])
    filter_dates = dates if dates is not None else ([partition_value] if partition_value else None)
    if filter_dates and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(filter_dates))].copy()
    return df
