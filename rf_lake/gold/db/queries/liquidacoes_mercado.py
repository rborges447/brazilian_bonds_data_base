"""
Queries de leitura para LIQUIDACOES_MERCADO.
"""

from __future__ import annotations

from typing import Optional
import sqlite3

import pandas as pd

from rf_lake.gold.db.queries.common import apply_date_filters


def get_liquidacoes_mercado(
    conn: sqlite3.Connection,
    *,
    ref_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tipo_titulo: Optional[str] = None,
    data_vencimento: Optional[str] = None,
) -> pd.DataFrame:
    """
    Consulta dados de liquidações de mercado, com join em `TITULOS_PUBLICOS`.
    """
    sql = """
        SELECT
            tp.tipo_titulo,
            tp.data_vencimento,
            tp.expressao,
            tp.codigo_selic,
            tp.codigo_isin,
            tp.status,
            lm.data_referencia,
            lm.qtd_operacoes,
            lm.qtd_titulos,
            lm.pu_medio
        FROM LIQUIDACOES_MERCADO lm
        JOIN TITULOS_PUBLICOS tp
          ON lm.tipo_titulo = tp.tipo_titulo
         AND lm.data_vencimento = tp.data_vencimento
        WHERE 1=1
    """
    params: list = []

    sql, params = apply_date_filters(
        sql,
        params,
        date_col="lm.data_referencia",
        ref_date=ref_date,
        start_date=start_date,
        end_date=end_date,
    )

    if tipo_titulo:
        sql += " AND tp.tipo_titulo = ?"
        params.append(tipo_titulo)

    if data_vencimento:
        sql += " AND tp.data_vencimento = ?"
        params.append(data_vencimento)

    sql += " ORDER BY lm.data_referencia DESC, tp.tipo_titulo, tp.data_vencimento"

    return pd.read_sql_query(sql, conn, params=params)

