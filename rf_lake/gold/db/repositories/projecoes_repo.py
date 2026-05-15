"""
Repositório para tabela PROJECOES.
"""

from __future__ import annotations

import sqlite3


class ProjecoesRepo:
    @staticmethod
    def upsert(
        conn: sqlite3.Connection,
        *,
        indice: str,
        tipo_projecao: str,
        data_coleta: str,
        ref_month: str,
        variacao_projetada: float | None = None,
        data_validade: str | None = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO PROJECOES (
                indice, tipo_projecao, data_coleta, ref_month,
                variacao_projetada, data_validade
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(indice, tipo_projecao, ref_month, data_coleta)
            DO UPDATE SET
                variacao_projetada = excluded.variacao_projetada,
                data_validade = excluded.data_validade
            """,
            (indice, tipo_projecao, data_coleta, ref_month, variacao_projetada, data_validade),
        )

    @staticmethod
    def has_any(conn: sqlite3.Connection) -> bool:
        """Retorna True se a tabela PROJECOES tiver ao menos um registro."""
        row = conn.execute("SELECT 1 FROM PROJECOES LIMIT 1;").fetchone()
        return row is not None
