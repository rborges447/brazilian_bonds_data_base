"""
Read queries for LEILOES.
"""

from __future__ import annotations

from typing import Optional
import sqlite3

import pandas as pd

from rf_lake.gold.db.queries.common import apply_date_filters


def get_leiloes(
    conn: sqlite3.Connection,
    *,
    data_referencia: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tipo_titulo: Optional[str] = None,
    data_vencimento: Optional[str] = None,
    numero_edital: Optional[int] = None,
) -> pd.DataFrame:
    """
    Query auction data (results + offering) from LEILOES,
    with a join to TITULOS_PUBLICOS.
    """
    sql = """
        SELECT
            l.numero_edital,
            tp.tipo_titulo,
            tp.data_vencimento,
            l.data_referencia,
            l.oferta,
            l.quantidade_aceita,
            l.percentual_corte,
            l.oferta_segunda_volta,
            l.financeiro_aceito,
            l.financeiro_aceito_segunda_volta,
            l.quantidade_aceita_segunda_volta,
            l.pu_medio,
            l.taxa_media
        FROM LEILOES l
        JOIN TITULOS_PUBLICOS tp
          ON l.tipo_titulo = tp.tipo_titulo
         AND l.data_vencimento = tp.data_vencimento
        WHERE 1=1
    """
    params: list = []

    sql, params = apply_date_filters(
        sql,
        params,
        date_col="l.data_referencia",
        ref_date=data_referencia,
        start_date=start_date,
        end_date=end_date,
    )

    if tipo_titulo:
        sql += " AND l.tipo_titulo = ?"
        params.append(tipo_titulo)

    if data_vencimento:
        sql += " AND l.data_vencimento = ?"
        params.append(data_vencimento)

    if numero_edital is not None:
        sql += " AND l.numero_edital = ?"
        params.append(numero_edital)

    sql += " ORDER BY l.data_referencia DESC, l.numero_edital, tp.tipo_titulo"

    return pd.read_sql_query(sql, conn, params=params)

