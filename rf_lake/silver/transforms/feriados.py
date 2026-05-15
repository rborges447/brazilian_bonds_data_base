"""
Normalização de feriados (lista ou DataFrame -> DataFrame com coluna data em "YYYY-MM-DD").
"""

from __future__ import annotations

from typing import List, Union

import pandas as pd


def normalize(raw: Union[List[str], pd.DataFrame]) -> pd.DataFrame:
    """
    Normaliza entrada para DataFrame com coluna `data` em str "YYYY-MM-DD".

    - Se raw for lista de strings: assume já em "YYYY-MM-DD" (ou converte datetime).
    - Se raw for DataFrame: espera coluna "Data" ou "data"; normaliza para str "YYYY-MM-DD".
    - Remove duplicatas e ordena por data.
    """
    if raw is None:
        return pd.DataFrame(columns=["data"])

    if isinstance(raw, list):
        if not raw:
            return pd.DataFrame(columns=["data"])
        # Garantir str YYYY-MM-DD
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
        # Normalizar para str YYYY-MM-DD
        df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=["data"])

    df = df[["data"]].drop_duplicates().sort_values("data").reset_index(drop=True)
    df["data"] = df["data"].astype(str)
    return df
