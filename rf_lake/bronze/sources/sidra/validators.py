"""
Validações de dados do SIDRA (IPCA).
"""

from __future__ import annotations

import re

import pandas as pd


def validate_ipca_long(df: pd.DataFrame) -> bool:
    """
    Valida o DataFrame long canônico do IPCA.

    Regras:
    - Colunas obrigatórias presentes
    - VAR_CODIGO em {"2266", "63"}
    - DATA_CODIGO no formato YYYYMM
    """
    if df is None or df.empty:
        return False

    required_cols = ["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"]
    for c in required_cols:
        if c not in df.columns:
            return False

    var_ok = set(df["VAR_CODIGO"].astype("string").str.strip().dropna().unique()).issubset({"2266", "63"})
    if not var_ok:
        return False

    codes = df["DATA_CODIGO"].astype("string").str.strip().dropna()
    if not codes.map(lambda s: bool(re.fullmatch(r"\d{6}", str(s)))).all():
        return False

    # VALOR deve ser numérico (pode ter NaN, mas em geral não deveria)
    if "VALOR" in df.columns:
        # `is_numeric_dtype` não garante ausência de NaN; aceitamos NaN mas rejeitamos tipos não numéricos
        if not pd.api.types.is_numeric_dtype(df["VALOR"]):
            return False

    return True

