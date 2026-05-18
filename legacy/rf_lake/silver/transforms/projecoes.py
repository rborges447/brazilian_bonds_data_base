"""
Projection normalization for IPCA/IGP-M (ANBIMA).
"""

from __future__ import annotations

import pandas as pd

from rf_lake.gold.db.schema import (
    PROJECOES_NUMERIC,
    PROJECOES_RENAME_MAP,
)
from rf_lake.silver.normalize import normalize_date_columns, normalize_numeric_columns


def normalize(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    PROJECOES-specific normalization.

    - Rename mes_referencia -> ref_month
    - Normalize dates (data_coleta, data_validade) to ISO YYYY-MM-DD
    - Normalize variacao_projetada to float
    - Keep ref_month as string (MM/YYYY)
    - data_validade stays NULL when NaN/empty
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=[
            "indice", "tipo_projecao", "data_coleta", "ref_month",
            "variacao_projetada", "data_validade",
        ])

    df = df_raw.copy()

    df = df.rename(columns=PROJECOES_RENAME_MAP)
    df = normalize_date_columns(df, ["data_coleta", "data_validade"])
    df = normalize_numeric_columns(df, PROJECOES_NUMERIC, use_comma_decimal=False)

    # Strings: trim
    for col in ("indice", "tipo_projecao", "ref_month"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Ensure column set and order
    out_cols = ["indice", "tipo_projecao", "data_coleta", "ref_month", "variacao_projetada", "data_validade"]
    for c in out_cols:
        if c not in df.columns:
            df[c] = None
    df = df[out_cols]

    return df
