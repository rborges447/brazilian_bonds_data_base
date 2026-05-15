from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional

from rf_lake.gold.db.connection import get_conn


def get_max_date(table: str, date_col: str) -> Optional[str]:
    """
    Retorna MAX(date_col) da tabela no formato 'YYYY-MM-DD' (ou None se vazia).
    """
    sql = f"SELECT MAX({date_col}) FROM {table};"
    conn = get_conn()
    try:
        row = conn.execute(sql).fetchone()
        return row[0] if row and row[0] else None
    finally:
        conn.close()


def list_dates(
    start_date: str,
    end_date: Optional[str] = None,
    skip_weekends: bool = True,
    ) -> List[str]:
    """
    Lista datas de start_date até end_date (inclusive).
    end_date default: ontem.
    """
    if end_date is None:
        end_date = (date.today() - timedelta(days=1)).isoformat()

    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

    if start_dt > end_dt:
        return []

    out: List[str] = []
    cur = start_dt
    while cur <= end_dt:
        if (not skip_weekends) or (cur.weekday() < 5):
            out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def missing_dates_for_table(
    table: str,
    date_col: str,
    default_start: str = "2018-01-01",
    end_date: Optional[str] = None,
    skip_weekends: bool = True,
    ) -> List[str]:
    """
    Regra genérica:
    - Se tabela tem datas: começa no dia seguinte ao MAX(date_col)
    - Se não tem: começa em default_start
    """
    max_dt = get_max_date(table, date_col)
    if max_dt:
        start_dt = (datetime.strptime(max_dt, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
    else:
        start_dt = default_start

    return list_dates(start_dt, end_date=end_date, skip_weekends=skip_weekends)
