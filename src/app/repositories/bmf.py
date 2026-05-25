"""BMF contracts and adjustments repository."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.connection import commit, execute, get_connection
from app.database.schema import (
    AJUSTES_BMF_COLUMNS,
    CONTRATOS_BMF_COLUMNS,
    TABLE_AJUSTES_BMF,
    TABLE_CONTRATOS_BMF,
)
from app.database.sql import upsert_prefix
from app.repositories._df_upsert import upsert_dataframe


class BmfRepository:
    def upsert(self, df: pd.DataFrame, *, db_path: Any = None) -> int:
        if df is None or df.empty:
            return 0
        prefix = upsert_prefix()
        conn = get_connection(db_path)
        try:
            for _, row in df.iterrows():
                execute(
                    conn,
                    f"{prefix} {TABLE_CONTRATOS_BMF} (ticker, codigo_isin, data_vencimento) "
                    "VALUES (?, ?, ?)",
                    (
                        str(row["ticker"]),
                        row.get("codigo_isin")
                        if pd.notna(row.get("codigo_isin"))
                        else None,
                        str(row["data_vencimento"]),
                    ),
                )
            commit(conn)
        finally:
            conn.close()
        ajustes = df[list(AJUSTES_BMF_COLUMNS)].copy()
        return upsert_dataframe(
            TABLE_AJUSTES_BMF, ajustes, AJUSTES_BMF_COLUMNS, db_path=db_path
        )
