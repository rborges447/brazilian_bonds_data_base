"""
Repositório para operações na tabela AJUSTES_BMF.
"""
from __future__ import annotations

import sqlite3


class AjustesBmfRepo:
    """
    Repositório para operações CRUD na tabela AJUSTES_BMF.
    """
    
    @staticmethod
    def upsert(conn: sqlite3.Connection,
               ticker: str,
               data_referencia: str,
               taxa_ajuste: float | None = None,
               quantidade_ajuste: float | None = None) -> None:
        """
        Insere ou atualiza um registro de ajuste BMF.
        
        Args:
            conn: Conexão com o banco
            ticker: Ticker do contrato (FK para CONTRATOS_BMF)
            data_referencia: Data de referência no formato ISO (YYYY-MM-DD)
            taxa_ajuste: Taxa de ajuste
            quantidade_ajuste: Quantidade de ajuste
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
