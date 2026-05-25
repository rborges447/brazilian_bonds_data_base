"""PTAX repository."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.schema import PTAX_COLUMNS, TABLE_PTAX
from app.repositories._df_upsert import upsert_dataframe


class PtaxRepository:
    table_name: str = TABLE_PTAX

    def upsert(self, df: pd.DataFrame, *, db_path: Any = None) -> int:
        return upsert_dataframe(self.table_name, df, PTAX_COLUMNS, db_path=db_path)
