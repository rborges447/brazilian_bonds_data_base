"""Shared helpers for tabular pass-through materializers."""

from __future__ import annotations

import pandas as pd

# Default for titulos_publicos when silver has no status column (legacy load).
SQL_STATUS_DEFAULT = "ATIVO"


def prepare_tabular_output(
    df: pd.DataFrame,
    *,
    dataset: str,
    required_silver: tuple[str, ...],
    optional_silver: tuple[str, ...] = (),
    sql_defaults: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Select silver columns, apply SQL defaults for missing fields, return ordered frame."""
    for col in required_silver:
        if col not in df.columns:
            raise ValueError(
                f"Silver {dataset} must have column '{col}', got: {list(df.columns)}"
            )
    cols = list(required_silver)
    for col in optional_silver:
        if col in df.columns and col not in cols:
            cols.append(col)
    out = df[cols].copy()
    for col, value in (sql_defaults or {}).items():
        if col not in out.columns:
            out[col] = value
        if col not in cols:
            cols.append(col)
    return out[cols]
