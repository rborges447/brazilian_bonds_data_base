from __future__ import annotations

import pandas as pd

from pipelines.silver.normalize import normalize_date_columns, normalize_numeric_columns
from pipelines.silver.schemas import CDI_NUMERIC, CDI_RENAME_MAP


def normalize_partition(
    df_raw: pd.DataFrame,
    partition_value: str,
    dates: list[str] | None = None,
) -> pd.DataFrame:
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=["data_referencia", "cdi"])

    df = df_raw.copy()
    rename_map = {k: v for k, v in CDI_RENAME_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    df = normalize_numeric_columns(df, CDI_NUMERIC)
    df = normalize_date_columns(df, ["data_referencia"])

    cols = [c for c in ("data_referencia", "cdi") if c in df.columns]
    df = df[cols]

    filter_dates = dates if dates is not None else ([partition_value] if partition_value else None)
    if filter_dates and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(filter_dates))].copy()
    return df
