"""
Queries de leitura para CONTRATOS_BMF.
"""

from __future__ import annotations

from typing import Optional
import sqlite3

import pandas as pd


def get_contratos_bmf(conn: sqlite3.Connection, *, ticker: Optional[str] = None) -> pd.DataFrame:
    """
    Consulta contratos BMF (cadastro).
    """
    sql = """
        SELECT
            ticker,
            codigo_isin,
            data_vencimento
        FROM CONTRATOS_BMF
        WHERE 1=1
    """
    params: list = []

    if ticker:
        sql += " AND ticker = ?"
        params.append(ticker)

    sql += " ORDER BY ticker"

    return pd.read_sql_query(sql, conn, params=params)

