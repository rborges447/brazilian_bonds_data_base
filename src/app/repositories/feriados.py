"""FERIADOS repository — full snapshot replace."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.connection import commit, execute, get_connection
from app.database.schema import TABLE_FERIADOS, validate_dataframe_columns


class FeriadosRepository:
    table_name: str = TABLE_FERIADOS

    def replace_all(self, dates: list[str], *, db_path: Any = None) -> int:
        conn = get_connection(db_path)
        try:
            execute(conn, f"DELETE FROM {self.table_name}")
            if not dates:
                commit(conn)
                return 0
            rows = [(str(d).strip()[:10],) for d in dates]
            conn.executemany(
                f"INSERT INTO {self.table_name} (data) VALUES (?)",
                rows,
            )
            commit(conn)
            return len(rows)
        finally:
            conn.close()

    def upsert(self, value: list[str] | pd.DataFrame, *, db_path: Any = None) -> int:
        if isinstance(value, pd.DataFrame):
            validate_dataframe_columns(self.table_name, value, ("data",))
            dates = value["data"].astype(str).tolist()
        else:
            dates = list(value)
        return self.replace_all(dates, db_path=db_path)

    def list_dates(self, *, db_path: Any = None) -> list[str]:
        conn = get_connection(db_path)
        try:
            cur = execute(conn, f"SELECT data FROM {self.table_name} ORDER BY data")
            return [str(r[0]) for r in cur.fetchall()]
        finally:
            conn.close()
