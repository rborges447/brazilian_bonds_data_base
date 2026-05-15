from __future__ import annotations

import pandas as pd

from rf_lake.gold.db.schema import LIQUIDACOES_MERCADO_NUMERIC, LIQUIDACOES_MERCADO_RENAME_MAP
from rf_lake.silver.normalize import normalize_date_columns, normalize_numeric_columns


def normalize(df_raw: pd.DataFrame, dates: list[str] | None = None) -> pd.DataFrame:
    """
    Normalização específica de LIQUIDACOES_MERCADO (baseline do pipeline).

    - Renomeia colunas via `LIQUIDACOES_MERCADO_RENAME_MAP`
    - Normaliza numéricos pt-BR (vírgula decimal)
    - Normaliza datas para ISO
    - (Opcional) filtra `data_referencia ∈ dates` (guard rail para DATA MOV)
    """
    df = df_raw.copy()

    df = df.rename(columns=LIQUIDACOES_MERCADO_RENAME_MAP)
    df = normalize_numeric_columns(df, LIQUIDACOES_MERCADO_NUMERIC, use_comma_decimal=True)
    df = normalize_date_columns(df, ["data_referencia", "data_vencimento"])

    if dates is not None and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(dates))].copy()

    return df

