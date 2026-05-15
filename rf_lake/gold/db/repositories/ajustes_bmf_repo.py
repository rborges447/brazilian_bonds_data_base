"""
Repository for AJUSTES_BMF table operations.
"""
from __future__ import annotations

import sqlite3


class AjustesBmfRepo:
    """
    Repository for CRUD on AJUSTES_BMF.
    """
    
    @staticmethod
    def upsert(conn: sqlite3.Connection,
               ticker: str,
               data_referencia: str,
               taxa_ajuste: float | None = None,
               quantidade_ajuste: float | None = None) -> None:
        """
        Insert or update a BMF adjustment row.

        Args:
            conn: Database connection
            ticker: Contract ticker (FK to CONTRATOS_BMF)
            data_referencia: Reference date in ISO (YYYY-MM-DD)
            taxa_ajuste: Adjustment rate
            quantidade_ajuste: Adjustment quantity
        """
        conn.execute("""
            INSERT INTO AJUSTES_BMF (
                ticker, data_referencia,
                taxa_ajuste, quantidade_ajuste
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(ticker, data_referencia)
            DO UPDATE SET
            taxa_ajuste = excluded.taxa_ajuste,
            quantidade_ajuste = excluded.quantidade_ajuste
        """, (ticker, data_referencia, taxa_ajuste, quantidade_ajuste))
