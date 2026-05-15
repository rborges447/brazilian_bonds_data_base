"""
Read queries for table `schema_migrations`.
"""

from __future__ import annotations

import sqlite3

import pandas as pd


def get_schema_migrations(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Query the `schema_migrations` table.
    """
    sql = """
        SELECT version, applied_at
        FROM schema_migrations
        ORDER BY version
    """
    return pd.read_sql_query(sql, conn)

