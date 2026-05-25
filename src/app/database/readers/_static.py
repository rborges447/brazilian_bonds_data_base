"""Read dimension tables without market reference date."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.readers._execute import load_query, query_to_dataframe


class TitulosPublicosReader:
    """TITULOS_PUBLICOS: fetch_all and fetch_latest only."""

    def __init__(self, *, db_path: Any = None) -> None:
        self._db_path = db_path

    def fetch_all(self) -> pd.DataFrame:
        return query_to_dataframe(
            load_query("titulos_publicos_all"), (), db_path=self._db_path
        )

    def fetch_latest(self, n: int) -> pd.DataFrame:
        if n < 1:
            raise ValueError(f"n must be >= 1, got {n}")
        return query_to_dataframe(
            load_query("titulos_publicos_latest"), (n,), db_path=self._db_path
        )

    def fetch_on(self, date: str) -> pd.DataFrame:
        raise TypeError(
            "TITULOS_PUBLICOS has no data_referencia; use fetch_all() or fetch_latest(n)."
        )

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        raise TypeError(
            "TITULOS_PUBLICOS has no data_referencia; use fetch_all() or fetch_latest(n)."
        )


class ContratosBmfReader:
    """CONTRATOS_BMF: fetch_all and fetch_latest only."""

    def __init__(self, *, db_path: Any = None) -> None:
        self._db_path = db_path

    def fetch_all(self) -> pd.DataFrame:
        return query_to_dataframe(
            load_query("contratos_bmf_all"), (), db_path=self._db_path
        )

    def fetch_latest(self, n: int) -> pd.DataFrame:
        if n < 1:
            raise ValueError(f"n must be >= 1, got {n}")
        return query_to_dataframe(
            load_query("contratos_bmf_latest"), (n,), db_path=self._db_path
        )

    def fetch_on(self, date: str) -> pd.DataFrame:
        raise TypeError(
            "CONTRATOS_BMF has no data_referencia; use fetch_all() or fetch_latest(n)."
        )

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        raise TypeError(
            "CONTRATOS_BMF has no data_referencia; use fetch_all() or fetch_latest(n)."
        )
