"""LIQUIDACOES_MERCADO repository."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.connection import commit, get_connection
from app.database.schema import LIQUIDACOES_MERCADO_COLUMNS, TABLE_LIQUIDACOES_MERCADO
from app.repositories._df_upsert import upsert_dataframe
from app.repositories.titulos_publicos import TitulosPublicosRepository


class LiquidacoesMercadoRepository:
    table_name: str = TABLE_LIQUIDACOES_MERCADO

    def upsert(self, df: pd.DataFrame, *, db_path: Any = None) -> int:
        if df is None or df.empty:
            return 0
        titulos = TitulosPublicosRepository()
        conn = get_connection(db_path)
        try:
            for _, row in df.iterrows():
                titulos.get_or_create(
                    conn,
                    tipo_titulo=str(row["tipo_titulo"]),
                    data_vencimento=str(row["data_vencimento"]),
                    expressao=row.get("expressao") if pd.notna(row.get("expressao")) else None,
                    data_base=row.get("data_base") if pd.notna(row.get("data_base")) else None,
                    codigo_selic=row.get("codigo_selic")
                    if pd.notna(row.get("codigo_selic"))
                    else None,
                    codigo_isin=row.get("codigo_isin")
                    if pd.notna(row.get("codigo_isin"))
                    else None,
                    status=str(row.get("status", "ATIVO")),
                )
            commit(conn)
        finally:
            conn.close()
        return upsert_dataframe(
            self.table_name, df, LIQUIDACOES_MERCADO_COLUMNS, db_path=db_path
        )
