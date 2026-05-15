"""
Read queries for IPCA_INDICE.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import sqlite3

from rf_lake.gold.db.queries.common import apply_date_filters


def _first_day_iso(year: int, month: int) -> str:
    """Return the first day of the month as ISO YYYY-MM-DD (e.g. 2025-06-01)."""
    return f"{year:04d}-{month:02d}-01"


def get_ipca_indice(
    conn: sqlite3.Connection,
    *,
    ref_month: Optional[str] = None,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
    start_year: Optional[int] = None,
    start_month_num: Optional[int] = None,
    end_year: Optional[int] = None,
    end_month_num: Optional[int] = None,
    last: Optional[int] = None,
) -> pd.DataFrame:
    """
    Query monthly IPCA (IPCA_INDICE table).

    Modes (exclusive; priority order):
    - last=N: last N reference months.
    - start_year/start_month_num/end_year/end_month_num: year/month range (all four required for range).
    - ref_month or start_month/end_month (ISO YYYY-MM-DD): legacy behavior.
    - No filter: return all rows.

    ref_month, start_month, end_month are ISO YYYY-MM-DD strings (always day 01).
    """
    params: list = []

    if last is not None and last > 0:
        sql = """
            SELECT ref_month, ipca_index, ipca_mom
            FROM (
                SELECT ref_month, ipca_index, ipca_mom
                FROM IPCA_INDICE
                ORDER BY ref_month DESC
                LIMIT ?
            )
            ORDER BY ref_month ASC
        """
        return pd.read_sql_query(sql, conn, params=[int(last)])

    if (
        start_year is not None
        and start_month_num is not None
        and end_year is not None
        and end_month_num is not None
    ):
        start_date = _first_day_iso(start_year, start_month_num)
        end_date = _first_day_iso(end_year, end_month_num)
        sql = """
            SELECT ref_month, ipca_index, ipca_mom
            FROM IPCA_INDICE
            WHERE ref_month >= ? AND ref_month <= ?
            ORDER BY ref_month ASC
        """
        return pd.read_sql_query(sql, conn, params=[start_date, end_date])

    sql = """
        SELECT ref_month, ipca_index, ipca_mom
        FROM IPCA_INDICE
        WHERE 1=1
    """
    sql, params = apply_date_filters(
        sql,
        params,
        date_col="ref_month",
        ref_date=ref_month,
        start_date=start_month,
        end_date=end_month,
    )
    sql += " ORDER BY ref_month ASC"
    return pd.read_sql_query(sql, conn, params=params)


def get_ipca_indice_last_months(conn: sqlite3.Connection, *, months: int) -> pd.DataFrame:
    """
    Return the last `months` rows (oldest → newest).
    """
    if months <= 0:
        return pd.DataFrame(columns=["ref_month", "ipca_index", "ipca_mom"])
    return get_ipca_indice(conn, last=months)
