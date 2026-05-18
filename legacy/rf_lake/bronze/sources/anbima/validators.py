"""
Validate raw ANBIMA API data.
"""

from __future__ import annotations

import pandas as pd


def validate_mercado_secundario(df: pd.DataFrame) -> bool:
    """
    Check whether the secondary-market DataFrame has the expected shape.

    Args:
        df: DataFrame to validate

    Returns:
        True if valid, False otherwise
    """
    if df is None or df.empty:
        return False

    # Basic checks can be added here (e.g. required columns)

    return True
