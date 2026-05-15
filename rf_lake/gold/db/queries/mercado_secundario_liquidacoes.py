"""
Combined query: MERCADO_SECUNDARIO + LIQUIDACOES_MERCADO (LEFT JOIN) with TITULOS_PUBLICOS.
Returns taxa_anbima and qtd_titulos (and other columns) in one DataFrame.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import sqlite3

from rf_lake.gold.db.queries.common import apply_date_filters


def get_mercado_secundario_com_liquidacoes(
    conn: sqlite3.Connection,
    *,
    ref_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tipo_titulo: Optional[str] = None,
    data_vencimento: Optional[str] = None,
) -> pd.DataFrame:
    """
    Query secondary market and settlements in one DataFrame.

    MERCADO_SECUNDARIO (base) LEFT JOIN LIQUIDACOES_MERCADO on
    (tipo_titulo, data_vencimento, data_referencia), with TITULOS_PUBLICOS.
    Settlement columns (qtd_operacoes, qtd_titulos, pu_medio) are NULL
    when there is no settlement on the same day.
    """
    sql = """
        SELECT
            tp.tipo_titulo,
            tp.data_vencimento,
            tp.expressao,
            tp.codigo_selic,
            tp.codigo_isin,
            tp.status,
            ms.data_referencia,
            ms.taxa_anbima,
            ms.intervalo_min_d0,
            ms.intervalo_max_d0,
            ms.intervalo_min_d1,
            ms.intervalo_max_d1,
            ms.pu,
            lm.qtd_operacoes,
            lm.qtd_titulos,
            lm.pu_medio
        FROM MERCADO_SECUNDARIO ms
        JOIN TITULOS_PUBLICOS tp
          ON ms.tipo_titulo = tp.tipo_titulo
         AND ms.data_vencimento = tp.data_vencimento
        LEFT JOIN LIQUIDACOES_MERCADO lm
          ON ms.tipo_titulo = lm.tipo_titulo
         AND ms.data_vencimento = lm.data_vencimento
         AND ms.data_referencia = lm.data_referencia
        WHERE 1=1
    """
    params: list = []

    sql, params = apply_date_filters(
        sql,
        params,
        date_col="ms.data_referencia",
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

    sql += " ORDER BY ms.data_referencia DESC, tp.tipo_titulo, tp.data_vencimento"

    return pd.read_sql_query(sql, conn, params=params)
