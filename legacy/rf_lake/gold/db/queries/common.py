from __future__ import annotations

from typing import Optional


def apply_date_filters(
    sql: str,
    params: list,
    *,
    date_col: str,
    ref_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> tuple[str, list]:
    """
    Apply date filters (ISO YYYY-MM-DD) to SQL.

    Rules:
    - if `ref_date` is set, `start_date`/`end_date` must not be set
    - `start_date` and/or `end_date` define an inclusive range
    - if none are set, no date filter is applied
    """
    if ref_date is not None and (start_date is not None or end_date is not None):
        raise ValueError("Use either `ref_date` OR (`start_date`/`end_date`).")

    if ref_date is not None:
        sql += f" AND {date_col} = ?"
        params.append(ref_date)
        return sql, params

    if start_date is not None:
        sql += f" AND {date_col} >= ?"
        params.append(start_date)

    if end_date is not None:
        sql += f" AND {date_col} <= ?"
        params.append(end_date)

    return sql, params

