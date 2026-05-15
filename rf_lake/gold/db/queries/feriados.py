"""
Queries de leitura para FERIADOS.
"""

from __future__ import annotations

import sqlite3

import pandas as pd


def get_feriados(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Consulta todos os feriados (coluna data em str "YYYY-MM-DD"), ordenados por data.
    """
    sql = "SELECT data FROM FERIADOS ORDER BY data"
    df = pd.read_sql_query(sql, conn)
    if not df.empty:
        df["data"] = df["data"].astype(str)
    return df
