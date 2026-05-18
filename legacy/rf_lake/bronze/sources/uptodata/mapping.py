"""
Map UpToData files to the canonical schema.
"""

from __future__ import annotations

import pandas as pd


def filtro_DI_DAP(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only DI/DAP contract rows.

    Args:
        df: Raw BMF adjustments DataFrame

    Returns:
        Filtered DataFrame
    """
    if df is None or df.empty or 'TckrSymb' not in df.columns:
        return df

    return df[df['TckrSymb'].str.startswith(('DAP', 'DI1'))]


def map_ajustes_bmf_to_canonical(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Map raw UpToData DataFrame to canonical format.

    Args:
        df_raw: Raw UpToData DataFrame

    Returns:
        Canonical-format DataFrame
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    df = filtro_DI_DAP(df_raw.copy())

    return df
