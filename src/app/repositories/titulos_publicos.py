"""TITULOS_PUBLICOS dimension repository."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.connection import commit, execute, get_connection
from app.database.schema import TABLE_TITULOS_PUBLICOS, TITULOS_PUBLICOS_COLUMNS
from app.database.sql import upsert_prefix


class TitulosPublicosRepository:
    table_name: str = TABLE_TITULOS_PUBLICOS

    def get_or_create(
        self,
        conn: Any,
        *,
        tipo_titulo: str,
        data_vencimento: str,
        expressao: str | None = None,
        data_base: str | None = None,
        codigo_selic: str | None = None,
        codigo_isin: str | None = None,
        status: str = "ATIVO",
    ) -> None:
        prefix = upsert_prefix()
        sql = (
            f"{prefix} {self.table_name} "
            "(tipo_titulo, data_vencimento, expressao, data_base, codigo_selic, codigo_isin, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        execute(
            conn,
            sql,
            (
                tipo_titulo,
                data_vencimento,
                expressao,
                data_base,
                codigo_selic,
                codigo_isin,
                status,
            ),
        )

    def upsert_from_dataframe(self, df: pd.DataFrame, *, db_path: Any = None) -> int:
        if df is None or df.empty:
            return 0
        conn = get_connection(db_path)
        try:
            n = 0
            for _, row in df.iterrows():
                self.get_or_create(
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
                n += 1
            commit(conn)
            return n
        finally:
            conn.close()
