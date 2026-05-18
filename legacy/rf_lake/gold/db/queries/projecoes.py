"""
Read queries for PROJECOES.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import sqlite3

from rf_lake.gold.db.queries.common import apply_date_filters

# SQL expression to sort ref_month (MM/YYYY) as year*12+month
_REF_MONTH_ORDINAL = (
    "(CAST(SUBSTR(ref_month, 4) AS INTEGER) * 12 + CAST(SUBSTR(ref_month, 1, 2) AS INTEGER))"
)


def get_projecoes(
    conn: sqlite3.Connection,
    *,
    indice: Optional[str] = None,
    ref_month: Optional[str] = None,
    start_data_coleta: Optional[str] = None,
    end_data_coleta: Optional[str] = None,
    start_year: Optional[int] = None,
    start_month: Optional[int] = None,
    end_year: Optional[int] = None,
    end_month: Optional[int] = None,
    last: Optional[int] = None,
) -> pd.DataFrame:
    """
    Query projections (PROJECOES table).

    Modes for ref_month (exclusive; priority order):
    - last=N: last N distinct ref_month values.
    - start_year/start_month/end_year/end_month: ref_month range (all four required).
    - ref_month (exact MM/YYYY string): a single month.
    - No period filter: all ref_month values.

    data_coleta in ISO YYYY-MM-DD. ref_month in MM/YYYY format.
    """
    params: list = []
    base_select = """
        SELECT
            indice,
            tipo_projecao,
            data_coleta,
            ref_month,
            variacao_projetada,
            data_validade
        FROM PROJECOES
        WHERE 1=1
    """

    if last is not None and last > 0:
        subquery = f"""
            SELECT ref_month FROM (
                SELECT DISTINCT ref_month FROM PROJECOES
                ORDER BY {_REF_MONTH_ORDINAL} DESC
                LIMIT ?
            )
        """
        sql = base_select + " AND ref_month IN (" + subquery.replace("\n", " ").strip() + ")"
        params.append(int(last))
        if indice is not None:
            sql = sql.replace("WHERE 1=1", "WHERE 1=1 AND indice = ?")
            params.insert(0, indice)
        sql, params = apply_date_filters(
            sql, params, date_col="data_coleta",
            start_date=start_data_coleta, end_date=end_data_coleta,
        )
        sql += " ORDER BY data_coleta DESC, " + _REF_MONTH_ORDINAL + " ASC, indice ASC, tipo_projecao ASC"
        return pd.read_sql_query(sql, conn, params=params)

    if (
        start_year is not None
        and start_month is not None
        and end_year is not None
        and end_month is not None
    ):
        start_val = start_year * 12 + start_month
        end_val = end_year * 12 + end_month
        sql = base_select + f" AND {_REF_MONTH_ORDINAL} >= ? AND {_REF_MONTH_ORDINAL} <= ?"
        params.extend([start_val, end_val])
        if indice is not None:
            sql = sql.replace("WHERE 1=1", "WHERE 1=1 AND indice = ?")
            params.insert(0, indice)
        sql, params = apply_date_filters(
            sql, params, date_col="data_coleta",
            start_date=start_data_coleta, end_date=end_data_coleta,
        )
        sql += " ORDER BY data_coleta DESC, " + _REF_MONTH_ORDINAL + " ASC, indice ASC, tipo_projecao ASC"
        return pd.read_sql_query(sql, conn, params=params)

    sql = base_select
    if indice is not None:
        sql += " AND indice = ?"
        params.append(indice)
    if ref_month is not None:
        sql += " AND ref_month = ?"
        params.append(ref_month)
    sql, params = apply_date_filters(
        sql,
        params,
        date_col="data_coleta",
        start_date=start_data_coleta,
        end_date=end_data_coleta,
    )
    sql += " ORDER BY data_coleta DESC, " + _REF_MONTH_ORDINAL + " ASC, indice ASC, tipo_projecao ASC"
    return pd.read_sql_query(sql, conn, params=params)
