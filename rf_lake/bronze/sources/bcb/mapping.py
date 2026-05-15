"""
Map raw BCB API data to the canonical schema.
"""

from __future__ import annotations

import pandas as pd


def map_negociacoes_to_canonical(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Map raw BCB trades DataFrame to canonical format.

    Args:
        df_raw: Raw BCB DataFrame

    Returns:
        Canonical-format DataFrame
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    # Pass-through for now; ETL pipelines may apply further mapping
    return df_raw.copy()
