"""
Read queries for table `job_runs`.
"""

from __future__ import annotations

from typing import Optional
import sqlite3

import pandas as pd

from rf_lake.gold.db.queries.common import apply_date_filters


def get_job_runs(
    conn: sqlite3.Connection,
    *,
    pipeline_name: Optional[str] = None,
    ref_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
) -> pd.DataFrame:
    """
    Query the `job_runs` table.
    """
    sql = """
        SELECT
            id,
            pipeline_name,
            ref_date,
            started_at,
            finished_at,
            status,
            rows_processed,
            error_message
        FROM job_runs
        WHERE 1=1
    """
    params: list = []

    sql, params = apply_date_filters(
        sql,
        params,
        date_col="ref_date",
        ref_date=ref_date,
        start_date=start_date,
        end_date=end_date,
    )

    if pipeline_name:
        sql += " AND pipeline_name = ?"
        params.append(pipeline_name)

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY started_at DESC"

    return pd.read_sql_query(sql, conn, params=params)

