from __future__ import annotations

import pandas as pd

from pipelines.silver.mappers.uptodata import filtro_di_dap
from pipelines.silver.normalize import (
    normalize_date_columns,
    normalize_numeric_columns,
    remove_duplicate_columns,
)
from pipelines.silver.schemas import AJUSTES_BMF_NUMERIC, AJUSTES_BMF_RENAME_MAP


def normalize_partition(
    df_raw: pd.DataFrame,
    partition_value: str,
    dates: list[str] | None = None,
) -> pd.DataFrame:
    df = df_raw.copy()
    if "TckrSymb" in df.columns:
        df = filtro_di_dap(df)
    df = remove_duplicate_columns(df)
    if "data_referencia" in df.columns and "RptDt" in df.columns:
        df = df.drop(columns=["RptDt"])
    rename_map = {k: v for k, v in AJUSTES_BMF_RENAME_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    df = remove_duplicate_columns(df)
    df = normalize_numeric_columns(df, AJUSTES_BMF_NUMERIC, use_comma_decimal=True)
    df = normalize_date_columns(df, ["data_referencia", "data_vencimento"])
    filter_dates = dates if dates is not None else ([partition_value] if partition_value else None)
    if filter_dates and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(filter_dates))].copy()
    return df
