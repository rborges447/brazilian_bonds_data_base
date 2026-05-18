"""
Read queries for TITULOS_PUBLICOS.
"""

from __future__ import annotations

from typing import Optional
import sqlite3

import pandas as pd


def get_titulos_publicos(
    conn: sqlite3.Connection,
    *,
    tipo_titulo: Optional[str] = None,
    data_vencimento: Optional[str] = None,
    status: Optional[str] = None,
) -> pd.DataFrame:
    """
    Query government bonds (reference / master data).
    """
    sql = """
        SELECT
            tipo_titulo,
            data_vencimento,
            expressao,
            data_base,
            codigo_selic,
            codigo_isin,
            status
        FROM TITULOS_PUBLICOS
        WHERE 1=1
    """
    params: list = []

    if tipo_titulo:
        sql += " AND tipo_titulo = ?"
        params.append(tipo_titulo)

    if data_vencimento:
        sql += " AND data_vencimento = ?"
        params.append(data_vencimento)

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY tipo_titulo, data_vencimento"

    return pd.read_sql_query(sql, conn, params=params)

