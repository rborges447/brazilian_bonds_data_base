from __future__ import annotations

import pandas as pd

from app.lake.silver.normalize import normalize_date_columns, normalize_numeric_columns
from app.lake.silver.schemas import LEILOES_NUMERIC, LEILOES_RENAME_MAP


def normalize_partition(
    df_raw: pd.DataFrame,
    partition_value: str,
    dates: list[str] | None = None,
) -> pd.DataFrame:
    df = df_raw.copy()
    df = df.rename(columns=LEILOES_RENAME_MAP)
    df = normalize_date_columns(df, ["data_referencia", "data_vencimento"])
    iso_re = r"^\d{4}-\d{2}-\d{2}$"
    if "data_referencia" in df.columns and "data_vencimento" in df.columns:
        mask_ref = df["data_referencia"].notna() & df["data_referencia"].astype(str).str.match(iso_re)
        mask_venc = df["data_vencimento"].notna() & df["data_vencimento"].astype(str).str.match(iso_re)
        df = df[mask_ref & mask_venc]
    filter_dates = dates if dates is not None else ([partition_value] if partition_value else None)
    if filter_dates and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(filter_dates))].copy()
    df = normalize_numeric_columns(df, LEILOES_NUMERIC)
    return df
