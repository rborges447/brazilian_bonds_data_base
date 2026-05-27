"""VNA repository."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.schema import TABLE_VNA, VNA_COLUMNS
from app.repositories._df_upsert import upsert_dataframe


class VnaRepository:
    table_name: str = TABLE_VNA

    def upsert(self, df: pd.DataFrame, *, db_path: Any = None) -> int:
        return upsert_dataframe(self.table_name, df, VNA_COLUMNS, db_path=db_path)
