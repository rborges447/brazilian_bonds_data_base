import sqlite3
from typing import Optional, Tuple


class LeiloesRepo:
    @staticmethod
    def upsert(
        conn: sqlite3.Connection,
        numero_edital: int,
        tipo_titulo: str,
        data_vencimento: str,
        data_referencia: str,
        oferta: Optional[int] = None,
        quantidade_aceita: Optional[int] = None,
        percentual_corte: Optional[float] = None,
        oferta_segunda_volta: Optional[int] = None,
        financeiro_aceito: Optional[float] = None,
        financeiro_aceito_segunda_volta: Optional[float] = None,
        quantidade_aceita_segunda_volta: Optional[int] = None,
        pu_medio: Optional[float] = None,
        taxa_media: Optional[float] = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO LEILOES (
                numero_edital, tipo_titulo, data_vencimento, data_referencia,
                oferta,
                quantidade_aceita, percentual_corte, oferta_segunda_volta,
                financeiro_aceito, financeiro_aceito_segunda_volta,
                quantidade_aceita_segunda_volta, pu_medio, taxa_media
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tipo_titulo, data_vencimento, data_referencia, numero_edital)
            DO UPDATE SET
                oferta = excluded.oferta,
                quantidade_aceita = excluded.quantidade_aceita,
                percentual_corte = excluded.percentual_corte,
                oferta_segunda_volta = excluded.oferta_segunda_volta,
                financeiro_aceito = excluded.financeiro_aceito,
                financeiro_aceito_segunda_volta = excluded.financeiro_aceito_segunda_volta,
                quantidade_aceita_segunda_volta = excluded.quantidade_aceita_segunda_volta,
                pu_medio = excluded.pu_medio,
                taxa_media = excluded.taxa_media
            """,
            (
                numero_edital,
                tipo_titulo,
                data_vencimento,
                data_referencia,
                oferta,
                quantidade_aceita,
                percentual_corte,
                oferta_segunda_volta,
                financeiro_aceito,
                financeiro_aceito_segunda_volta,
                quantidade_aceita_segunda_volta,
                pu_medio,
                taxa_media,
            ),
        )

    @staticmethod
    def get_by_key(
        conn: sqlite3.Connection,
        numero_edital: int,
        tipo_titulo: str,
        data_vencimento: str,
        data_referencia: str,
    ) -> Optional[Tuple]:
        row = conn.execute(
            """
            SELECT
                numero_edital, tipo_titulo, data_vencimento, data_referencia,
                oferta,
                quantidade_aceita, percentual_corte, oferta_segunda_volta,
                financeiro_aceito, financeiro_aceito_segunda_volta,
                quantidade_aceita_segunda_volta, pu_medio, taxa_media
            FROM LEILOES
            WHERE tipo_titulo = ?
              AND data_vencimento = ?
              AND data_referencia = ?
              AND numero_edital = ?
            """,
            (tipo_titulo, data_vencimento, data_referencia, numero_edital),
        ).fetchone()
        return row

