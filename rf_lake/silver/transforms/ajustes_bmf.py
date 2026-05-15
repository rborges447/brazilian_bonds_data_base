from __future__ import annotations

import pandas as pd

from rf_lake.gold.db.schema import AJUSTES_BMF_NUMERIC, AJUSTES_BMF_RENAME_MAP
from rf_lake.silver.normalize import normalize_date_columns, normalize_numeric_columns, remove_duplicate_columns
from rf_lake.bronze.sources.uptodata.mapping import filtro_DI_DAP


def normalize(df_raw: pd.DataFrame, dates: list[str] | None = None) -> pd.DataFrame:
    """
    Normalização específica de AJUSTES_BMF (baseline do pipeline/notebook).

    - Filtra para DI/DAP (quando `TckrSymb` existir)
    - Remove colunas duplicadas
    - Renomeia colunas via `AJUSTES_BMF_RENAME_MAP`
    - Normaliza numéricos pt-BR (vírgula decimal)
    - Normaliza datas para ISO
    - (Opcional) filtra `data_referencia ∈ dates`
    """
    df = df_raw.copy()

    # Filtro DI/DAP (antes do rename: usa `TckrSymb`)
    if "TckrSymb" in df.columns:
        df = filtro_DI_DAP(df)

    # Remover colunas duplicadas antes de renomear
    df = remove_duplicate_columns(df)

    # Se já existe data_referencia e RptDt, remover RptDt antes do rename
    if "data_referencia" in df.columns and "RptDt" in df.columns:
        df = df.drop(columns=["RptDt"])

    # Renomear colunas (somente as presentes)
    rename_map = {k: v for k, v in AJUSTES_BMF_RENAME_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Remover colunas duplicadas após renomear
    df = remove_duplicate_columns(df)

    df = normalize_numeric_columns(df, AJUSTES_BMF_NUMERIC, use_comma_decimal=True)
    df = normalize_date_columns(df, ["data_referencia", "data_vencimento"])

    if dates is not None and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(dates))].copy()

    return df

