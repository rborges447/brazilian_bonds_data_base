"""
Repository for FERIADOS table.
"""

from __future__ import annotations

import sqlite3


class FeriadosRepo:
    @staticmethod
    def replace_all(conn: sqlite3.Connection, datas: list[str]) -> None:
        """
        Replace all rows in FERIADOS with the given dates.
        Each date must be a "YYYY-MM-DD" string.
        """
        conn.execute("DELETE FROM FERIADOS")
        if datas:
            conn.executemany(
                "INSERT INTO FERIADOS (data) VALUES (?)",
                [(d,) for d in datas],
            )

    @staticmethod
    def has_any(conn: sqlite3.Connection) -> bool:
        """Return True if FERIADOS has at least one row."""
        row = conn.execute("SELECT 1 FROM FERIADOS LIMIT 1;").fetchone()
        return row is not None
