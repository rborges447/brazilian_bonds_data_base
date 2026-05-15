"""
Map ANBIMA API payloads to canonical column layouts.
"""

from __future__ import annotations

import pandas as pd


def api_list_to_df(dados: list) -> pd.DataFrame:
    """
    Turn a list of ANBIMA API dict batches into one DataFrame.

    Args:
        dados: List of API responses (each item is a list of records for one day)

    Returns:
        DataFrame with all records concatenated
    """
    registros = [
        item
        for lista_do_dia in dados
        for item in (lista_do_dia or [])
        if isinstance(item, dict)
    ]

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame.from_records(registros)

    return df


def projecoes_to_df(dados: list) -> pd.DataFrame:
    """
    Turn a list of projection dicts into a flat DataFrame.

    Args:
        dados: List of dicts from ANBIMA projections API.
               May be a flat list or list-of-lists (as returned by fetch_projecoes_historico).

    Returns:
        DataFrame with columns: indice, tipo_projecao, data_coleta, mes_referencia,
        variacao_projetada, data_validade (when present).
    """
    if not dados:
        return pd.DataFrame()

    # List-of-lists (fetch_projecoes_historico): flatten
    if dados and isinstance(dados[0], list):
        dados = [item for sublist in dados for item in sublist]

    # Keep valid dicts only
    registros = [item for item in dados if isinstance(item, dict)]

    if not registros:
        return pd.DataFrame()

    return pd.DataFrame.from_records(registros)

