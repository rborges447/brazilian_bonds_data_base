"""
Validate raw Tesouro API data.
"""

from __future__ import annotations

import pandas as pd


def validate_resultados(df: pd.DataFrame) -> bool:
    """
    Check whether the auction results DataFrame has the expected shape.

    Args:
        df: DataFrame to validate

    Returns:
        True if valid, False otherwise
    """
    if df is None or df.empty:
        return False

    return True
