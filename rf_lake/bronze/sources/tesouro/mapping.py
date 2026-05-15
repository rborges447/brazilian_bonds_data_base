"""
Map Tesouro API data to the canonical schema.
"""

from __future__ import annotations

import pandas as pd


def map_tesouro_to_canonical(data: list) -> pd.DataFrame:
    """
    Map a list of auction result dicts to a canonical DataFrame.

    Args:
        data: List of result dicts

    Returns:
        Canonical-format DataFrame
    """
    if not data:
        return pd.DataFrame()

    valid_records = [
        record for record in data
        if isinstance(record, dict) and record
    ]

    if not valid_records:
        return pd.DataFrame()

    df = pd.DataFrame.from_records(valid_records)

    return df
