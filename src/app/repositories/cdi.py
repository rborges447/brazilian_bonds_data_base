"""CDI repository."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.schema import CDI_COLUMNS, TABLE_CDI
from app.repositories._df_upsert import upsert_dataframe


class CdiRepository:
    table_name: str = TABLE_CDI

    def upsert(self, df: pd.DataFrame, *, db_path: Any = None) -> int:
        return upsert_dataframe(self.table_name, df, CDI_COLUMNS, db_path=db_path)
