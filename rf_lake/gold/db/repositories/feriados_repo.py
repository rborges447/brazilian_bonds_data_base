"""
Repositório para tabela FERIADOS.
"""

from __future__ import annotations

import sqlite3


class FeriadosRepo:
    @staticmethod
    def replace_all(conn: sqlite3.Connection, datas: list[str]) -> None:
        """
        Substitui todo o conteúdo da tabela FERIADOS pelas datas fornecidas.
        Cada data deve ser string "YYYY-MM-DD".
        """
        conn.execute("DELETE FROM FERIADOS")
        if datas:
            conn.executemany(
                "INSERT INTO FERIADOS (data) VALUES (?)",
                [(d,) for d in datas],
            )

    @staticmethod
    def has_any(conn: sqlite3.Connection) -> bool:
        """Retorna True se a tabela FERIADOS tiver ao menos um registro."""
        row = conn.execute("SELECT 1 FROM FERIADOS LIMIT 1;").fetchone()
        return row is not None
