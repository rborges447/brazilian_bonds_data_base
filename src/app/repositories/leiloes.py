"""LEILOES repository."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.connection import commit, get_connection
from app.database.schema import LEILOES_COLUMNS, TABLE_LEILOES
from app.repositories._df_upsert import upsert_dataframe
from app.repositories.titulos_publicos import TitulosPublicosRepository


class LeiloesRepository:
    table_name: str = TABLE_LEILOES

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
                )
            commit(conn)
        finally:
            conn.close()
        return upsert_dataframe(self.table_name, df, LEILOES_COLUMNS, db_path=db_path)
