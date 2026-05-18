"""
SIDRA (IPCA) data validation.
"""

from __future__ import annotations

import re

import pandas as pd


def validate_ipca_long(df: pd.DataFrame) -> bool:
    """
    Validate the canonical long-format IPCA DataFrame.

    Rules:
    - Required columns present
    - VAR_CODIGO in {"2266", "63"}
    - DATA_CODIGO in YYYYMM form
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

    # VALOR should be numeric (NaNs allowed; reject non-numeric dtypes)
    if "VALOR" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["VALOR"]):
            return False

    return True
