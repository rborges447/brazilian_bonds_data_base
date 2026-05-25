"""Shared DataFrame → SQLite upsert helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.connection import commit, execute, get_connection
from app.database.schema import validate_dataframe_columns
from app.database.sql import upsert_prefix


def upsert_dataframe(
    table: str,
    df: pd.DataFrame,
    columns: tuple[str, ...],
    *,
    db_path: Any = None,
) -> int:
    if df is None or df.empty:
        return 0
    validate_dataframe_columns(table, df, columns)
    subset = df[list(columns)].copy()
    prefix = upsert_prefix()
    placeholders = ", ".join("?" for _ in columns)
    col_list = ", ".join(columns)
    sql = f"{prefix} {table} ({col_list}) VALUES ({placeholders})"
    conn = get_connection(db_path)
    try:
        rows = [tuple(row[c] for c in columns) for _, row in subset.iterrows()]
        conn.executemany(sql, rows)
        commit(conn)
        return len(rows)
    finally:
        conn.close()
