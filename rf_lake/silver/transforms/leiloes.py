from __future__ import annotations

import pandas as pd

from rf_lake.gold.db.schema import LEILOES_NUMERIC, LEILOES_RENAME_MAP
from rf_lake.silver.normalize import normalize_date_columns, normalize_numeric_columns


def normalize(df_raw: pd.DataFrame, dates: list[str] | None = None) -> pd.DataFrame:
    """
    Normalização específica de LEILOES (baseline do pipeline/notebook).

    - Renomeia colunas via `LEILOES_RENAME_MAP`
    - Normaliza datas e garante ISO
    - Se `dates` for fornecido, filtra `data_referencia ∈ dates` (porque o extract pode trazer o ano inteiro)
    - Normaliza numéricos (inclui `oferta`)
    """
    df = df_raw.copy()

    df = df.rename(columns=LEILOES_RENAME_MAP)

    df = normalize_date_columns(df, ["data_referencia", "data_vencimento"])

    # Garantia: datas em ISO
    iso_re = r"^\d{4}-\d{2}-\d{2}$"
    if "data_referencia" in df.columns and "data_vencimento" in df.columns:
        mask_ref_iso = df["data_referencia"].notna() & df["data_referencia"].astype(str).str.match(iso_re)
        mask_venc_iso = df["data_vencimento"].notna() & df["data_vencimento"].astype(str).str.match(iso_re)
        df = df[mask_ref_iso & mask_venc_iso]

    if dates is not None and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(dates))].copy()

    df = normalize_numeric_columns(df, LEILOES_NUMERIC)

    return df

