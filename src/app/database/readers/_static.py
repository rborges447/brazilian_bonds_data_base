"""Read snapshot / dimension tables (fetch_all only)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.readers._execute import load_query, query_to_dataframe

_FETCH_ALL_ONLY = "use fetch_all() only."


class FeriadosReader:
    """FERIADOS: full holiday calendar snapshot."""

    def __init__(self, *, db_path: Any = None) -> None:
        self._db_path = db_path

    def fetch_all(self) -> pd.DataFrame:
        return query_to_dataframe(
            load_query("feriados_all"), (), db_path=self._db_path
        )

    def fetch_latest(self, n: int) -> pd.DataFrame:
        raise TypeError(f"FERIADOS has no date-series API; {_FETCH_ALL_ONLY}")

    def fetch_on(self, date: str) -> pd.DataFrame:
        raise TypeError(f"FERIADOS has no date-series API; {_FETCH_ALL_ONLY}")

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        raise TypeError(f"FERIADOS has no date-series API; {_FETCH_ALL_ONLY}")


class TitulosPublicosReader:
    """TITULOS_PUBLICOS: full dimension snapshot."""

    def __init__(self, *, db_path: Any = None) -> None:
        self._db_path = db_path

    def fetch_all(self) -> pd.DataFrame:
        return query_to_dataframe(
            load_query("titulos_publicos_all"), (), db_path=self._db_path
        )

    def fetch_latest(self, n: int) -> pd.DataFrame:
        raise TypeError(f"TITULOS_PUBLICOS has no data_referencia; {_FETCH_ALL_ONLY}")

    def fetch_on(self, date: str) -> pd.DataFrame:
        raise TypeError(f"TITULOS_PUBLICOS has no data_referencia; {_FETCH_ALL_ONLY}")

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        raise TypeError(f"TITULOS_PUBLICOS has no data_referencia; {_FETCH_ALL_ONLY}")


class ContratosBmfReader:
    """CONTRATOS_BMF: full contracts snapshot."""

    def __init__(self, *, db_path: Any = None) -> None:
        self._db_path = db_path

    def fetch_all(self) -> pd.DataFrame:
        return query_to_dataframe(
            load_query("contratos_bmf_all"), (), db_path=self._db_path
        )

    def fetch_latest(self, n: int) -> pd.DataFrame:
        raise TypeError(f"CONTRATOS_BMF has no data_referencia; {_FETCH_ALL_ONLY}")

    def fetch_on(self, date: str) -> pd.DataFrame:
        raise TypeError(f"CONTRATOS_BMF has no data_referencia; {_FETCH_ALL_ONLY}")

    def fetch_range(self, start: str, end: str) -> pd.DataFrame:
        raise TypeError(f"CONTRATOS_BMF has no data_referencia; {_FETCH_ALL_ONLY}")
