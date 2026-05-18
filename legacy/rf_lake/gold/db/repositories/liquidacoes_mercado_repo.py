import sqlite3

class LiquidacoesMercadoRepo:
    @staticmethod
    def upsert(conn: sqlite3.Connection,
               tipo_titulo: str,
               data_vencimento: str,
               data_referencia: str,
               qtd_operacoes=None,
               qtd_titulos=None,
               pu_medio=None) -> None:
               
        conn.execute("""
            INSERT INTO LIQUIDACOES_MERCADO (
            tipo_titulo, data_vencimento, data_referencia,
            qtd_operacoes, qtd_titulos, pu_medio
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(tipo_titulo, data_vencimento, data_referencia)
            DO UPDATE SET
            qtd_operacoes = excluded.qtd_operacoes,
            qtd_titulos = excluded.qtd_titulos,
            pu_medio = excluded.pu_medio
        """, (tipo_titulo, data_vencimento, data_referencia, qtd_operacoes,
            qtd_titulos, pu_medio))
