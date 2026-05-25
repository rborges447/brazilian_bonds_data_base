"""IPCA_DICT repository."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.schema import IPCA_DICT_COLUMNS, TABLE_IPCA_DICT
from app.repositories._df_upsert import upsert_dataframe


class IpcaDictRepository:
    table_name: str = TABLE_IPCA_DICT

    def upsert(self, df: pd.DataFrame, *, db_path: Any = None) -> int:
        if df is None or df.empty:
            return 0
        out = df.copy()
        if "usa_fechado" in out.columns:
            out["usa_fechado"] = out["usa_fechado"].astype(int)
        return upsert_dataframe(
            self.table_name, out, IPCA_DICT_COLUMNS, db_path=db_path
        )
