"""
Holiday normalization (list or DataFrame -> DataFrame with `data` column "YYYY-MM-DD").
"""

from __future__ import annotations

from typing import List, Union

import pandas as pd


def normalize(raw: Union[List[str], pd.DataFrame]) -> pd.DataFrame:
    """
    Normalize input to a DataFrame with `data` column as str "YYYY-MM-DD".

    - If raw is a list of strings: assume already "YYYY-MM-DD" (or convert datetime).
    - If raw is a DataFrame: expect column "Data" or "data"; normalize to str "YYYY-MM-DD".
    - Drop duplicates and sort by date.
    """
    if raw is None:
        return pd.DataFrame(columns=["data"])

    if isinstance(raw, list):
        if not raw:
            return pd.DataFrame(columns=["data"])
        # Ensure str YYYY-MM-DD
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
        # Normalize to str YYYY-MM-DD
        df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=["data"])

    df = df[["data"]].drop_duplicates().sort_values("data").reset_index(drop=True)
    df["data"] = df["data"].astype(str)
    return df
