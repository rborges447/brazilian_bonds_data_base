from __future__ import annotations

import pandas as pd

from app.lake.silver.normalize import normalize_date_columns, normalize_numeric_columns
from app.lake.silver.schemas import PTAX_NUMERIC, PTAX_RENAME_MAP

_SILVER_COLS = ["data_referencia", "tipo", "moeda", "ptax_compra", "ptax_venda"]


def normalize_partition(
    df_raw: pd.DataFrame,
    partition_value: str,
    dates: list[str] | None = None,
) -> pd.DataFrame:
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=_SILVER_COLS)

    df = df_raw.copy()
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.strftime("%Y-%m-%d")

    if "tipo" in df.columns:
        df = df[df["tipo"].astype(str).str.strip() == "A"].copy()
    if "moeda" in df.columns:
        df = df[df["moeda"].astype(str).str.strip().str.upper() == "USD"].copy()

    drop_cols = [c for c in ("paridade_compra", "paridade_venda", "codigo") if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    rename_map = {k: v for k, v in PTAX_RENAME_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    df = normalize_numeric_columns(df, PTAX_NUMERIC)
    df = normalize_date_columns(df, ["data_referencia"])

    for c in _SILVER_COLS:
        if c not in df.columns:
            df[c] = None
    df = df[_SILVER_COLS]

    filter_dates = dates if dates is not None else ([partition_value] if partition_value else None)
    if filter_dates and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(filter_dates))].copy()
    return df
