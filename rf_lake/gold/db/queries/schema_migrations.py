"""
Queries de leitura para tabela `schema_migrations`.
"""

from __future__ import annotations

import sqlite3

import pandas as pd


def get_schema_migrations(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Consulta a tabela `schema_migrations`.
    """
    sql = """
        SELECT version, applied_at
        FROM schema_migrations
        ORDER BY version
    """
    return pd.read_sql_query(sql, conn)

