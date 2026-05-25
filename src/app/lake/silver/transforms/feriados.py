"""Holiday normalization to a single `data` column (YYYY-MM-DD)."""

from __future__ import annotations

import pandas as pd


def normalize_partition(
    df_raw: pd.DataFrame,
    partition_value: str,
    dates: list[str] | None = None,
) -> pd.DataFrame:
    del partition_value, dates
    return _normalize(df_raw)


def _normalize(raw: pd.DataFrame | list[str] | None) -> pd.DataFrame:
    if raw is None:
        return pd.DataFrame(columns=["data"])
    if isinstance(raw, list):
        if not raw:
            return pd.DataFrame(columns=["data"])
        out = []
        for x in raw:
            if isinstance(x, str):
                out.append(x)
            else:
                out.append(pd.Timestamp(x).strftime("%Y-%m-%d"))
        df = pd.DataFrame({"data": out})
    else:
        df = raw.copy()
        if df.empty:
            return pd.DataFrame(columns=["data"])
        if "Data" in df.columns and "data" not in df.columns:
            df = df.rename(columns={"Data": "data"})
        if "data" not in df.columns:
            return pd.DataFrame(columns=["data"])
        df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=["data"])

    df = df[["data"]].drop_duplicates().sort_values("data").reset_index(drop=True)
    df["data"] = df["data"].astype(str)
    return df
