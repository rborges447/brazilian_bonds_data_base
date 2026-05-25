"""Full outer read: MERCADO_SECUNDARIO + LIQUIDACOES_MERCADO per título/date."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.readers._execute import (
    load_query,
    normalize_iso_date,
    query_to_dataframe,
)


class MercadoLiquidacoesReader:
    """Mercado and liquidações combined (full outer on titulo + data_referencia)."""

    def __init__(self, *, db_path: Any = None) -> None:
        self._db_path = db_path

    def fetch_latest(self, n: int) -> pd.DataFrame:
        if n < 1:
            raise ValueError(f"n must be >= 1, got {n}")
        sql = load_query("mercado_liquidacoes_full_outer_latest")
        return query_to_dataframe(sql, (n,), db_path=self._db_path)

    def fetch_on(self, date: str) -> pd.DataFrame:
        d = normalize_iso_date(date)
        sql = load_query("mercado_liquidacoes_full_outer_on_date")
        return query_to_dataframe(sql, (d, d), db_path=self._db_path)

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        s = normalize_iso_date(start, param="start")
        e = normalize_iso_date(end, param="end")
        if s > e:
            raise ValueError(f"start must be <= end, got {s} > {e}")
        sql = load_query("mercado_liquidacoes_full_outer_range")
        return query_to_dataframe(sql, (s, e, s, e), db_path=self._db_path)

    def fetch_all(self) -> pd.DataFrame:
        sql = load_query("mercado_liquidacoes_full_outer_all")
        return query_to_dataframe(sql, (), db_path=self._db_path)
