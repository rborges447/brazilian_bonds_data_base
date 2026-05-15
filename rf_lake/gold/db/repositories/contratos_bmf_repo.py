"""
Repositório para operações na tabela CONTRATOS_BMF.
"""
from __future__ import annotations

import sqlite3
from typing import Optional


class ContratosBmfRepo:
    """
    Repositório para operações CRUD na tabela CONTRATOS_BMF.
    """
    
    @staticmethod
    def exists(conn: sqlite3.Connection, ticker: str) -> bool:
        """
        Verifica se um contrato com o ticker existe.
        
        Args:
            conn: Conexão com o banco
            ticker: Ticker do contrato
            
        Returns:
            True se existe, False caso contrário
        """
        row = conn.execute("""
            SELECT 1
            FROM CONTRATOS_BMF
            WHERE ticker = ?
        """, (ticker,)).fetchone()
        return row is not None
    
    @staticmethod
    def get_or_create(conn: sqlite3.Connection, ticker: str, 
                      codigo_isin: Optional[str] = None,
                      data_vencimento: Optional[str] = None) -> str:
        """
        Busca ou cria um contrato BMF. Retorna o ticker.
        
        Args:
            conn: Conexão com o banco
            ticker: Ticker do contrato (PK)
            codigo_isin: Código ISIN do contrato
            data_vencimento: Data de vencimento no formato ISO (YYYY-MM-DD)
            
        Returns:
            Ticker do contrato (sempre o mesmo que foi passado)
        """
        # Verifica se já existe
        if ContratosBmfRepo.exists(conn, ticker):
            return ticker
        
        # Cria novo contrato
        conn.execute("""
            INSERT INTO CONTRATOS_BMF (
                ticker, codigo_isin, data_vencimento
            ) VALUES (?, ?, ?)
        """, (ticker, codigo_isin, data_vencimento))
        
        return ticker
