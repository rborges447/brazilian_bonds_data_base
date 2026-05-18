"""
Read queries for FERIADOS.
"""

from __future__ import annotations

import sqlite3

import pandas as pd


def get_feriados(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Query all holidays (`data` column as str "YYYY-MM-DD"), ordered by date.
    """
    sql = "SELECT data FROM FERIADOS ORDER BY data"
    df = pd.read_sql_query(sql, conn)
    if not df.empty:
        df["data"] = df["data"].astype(str)
    return df
