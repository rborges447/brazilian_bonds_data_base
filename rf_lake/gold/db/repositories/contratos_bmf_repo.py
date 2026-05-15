"""
Repository for CONTRATOS_BMF table operations.
"""
from __future__ import annotations

import sqlite3
from typing import Optional


class ContratosBmfRepo:
    """
    Repository for CRUD on CONTRATOS_BMF.
    """
    
    @staticmethod
    def exists(conn: sqlite3.Connection, ticker: str) -> bool:
        """
        Return whether a contract exists for the ticker.

        Args:
            conn: Database connection
            ticker: Contract ticker

        Returns:
            True if it exists, False otherwise
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
        Get or create a BMF contract. Returns the ticker.

        Args:
            conn: Database connection
            ticker: Contract ticker (PK)
            codigo_isin: Contract ISIN
            data_vencimento: Maturity date in ISO (YYYY-MM-DD)

        Returns:
            The ticker (same as input)
        """
        # Check if it already exists
        if ContratosBmfRepo.exists(conn, ticker):
            return ticker
        
        # Insert new contract
        conn.execute("""
            INSERT INTO CONTRATOS_BMF (
                ticker, codigo_isin, data_vencimento
            ) VALUES (?, ?, ?)
        """, (ticker, codigo_isin, data_vencimento))
        
        return ticker
