"""Map ANBIMA projection payloads to flat DataFrames."""

from __future__ import annotations

import pandas as pd


def projecoes_to_df(dados: list) -> pd.DataFrame:
    if not dados:
        return pd.DataFrame()

    if dados and isinstance(dados[0], list):
        dados = [item for sublist in dados for item in sublist]

    registros = [item for item in dados if isinstance(item, dict)]
    if not registros:
        return pd.DataFrame()

    return pd.DataFrame.from_records(registros)
