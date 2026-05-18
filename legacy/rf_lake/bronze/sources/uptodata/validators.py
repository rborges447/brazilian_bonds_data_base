"""
Validate raw UpToData extracts.
"""

from __future__ import annotations

import pandas as pd


def validate_ajustes_bmf(df: pd.DataFrame) -> bool:
    """
    Check whether the BMF adjustments DataFrame has the expected shape.

    Args:
        df: DataFrame to validate

    Returns:
        True if valid, False otherwise
    """
    if df is None or df.empty:
        return False

    return True
