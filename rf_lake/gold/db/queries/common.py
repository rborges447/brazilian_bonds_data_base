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
    Aplica filtros de data (ISO YYYY-MM-DD) a um SQL.

    Regras:
    - se `ref_date` for fornecido, não pode haver `start_date`/`end_date`
    - `start_date` e/ou `end_date` definem um intervalo inclusivo
    - se nenhum for fornecido, não aplica filtro por data
    """
    if ref_date is not None and (start_date is not None or end_date is not None):
        raise ValueError("Use apenas `ref_date` OU (`start_date`/`end_date`).")

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

