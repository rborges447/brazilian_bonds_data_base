"""
Read queries for AJUSTES_BMF.
"""

from __future__ import annotations

from typing import Optional
import sqlite3

import pandas as pd

from rf_lake.gold.db.queries.common import apply_date_filters


def get_ajustes_bmf(
    conn: sqlite3.Connection,
    *,
    ref_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ticker: Optional[str] = None,
) -> pd.DataFrame:
    """
    Query BMF adjustment rows with a left join to `CONTRATOS_BMF` for reference data.
    """
    sql = """
        SELECT
            ab.ticker,
            ab.data_referencia,
            cb.codigo_isin,
            cb.data_vencimento,
            ab.taxa_ajuste,
            ab.quantidade_ajuste
        FROM AJUSTES_BMF ab
        LEFT JOIN CONTRATOS_BMF cb ON ab.ticker = cb.ticker
        WHERE 1=1
    """
    params: list = []

    sql, params = apply_date_filters(
        sql,
        params,
        date_col="ab.data_referencia",
        ref_date=ref_date,
        start_date=start_date,
        end_date=end_date,
    )

    if ticker:
        sql += " AND ab.ticker = ?"
        params.append(ticker)

    sql += " ORDER BY ab.data_referencia DESC, ab.ticker"

    return pd.read_sql_query(sql, conn, params=params)

