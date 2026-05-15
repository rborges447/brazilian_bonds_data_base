"""
Mapeamento de dados da API ANBIMA para formato canônico.
"""

from __future__ import annotations

import pandas as pd


def api_list_to_df(dados: list) -> pd.DataFrame:
    """
    Converte uma lista de dicionários da API ANBIMA em um DataFrame.
    
    Args:
        dados: Lista de respostas da API (cada item é uma lista de registros do dia)
        
    Returns:
        DataFrame com todos os registros concatenados
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
    Converte lista de projeções em DataFrame simples.
    Cada dicionário vira uma linha, cada chave vira uma coluna.
    
    Args:
        dados: Lista de dicionários com projeções da API ANBIMA.
               Pode ser uma lista simples de dicionários ou uma lista de listas
               (como retornado por fetch_projecoes_historico).
        
    Returns:
        DataFrame com colunas: indice, tipo_projecao, data_coleta, mes_referencia,
        variacao_projetada, data_validade (quando disponível).
    """
    if not dados:
        return pd.DataFrame()
    
    
    # Se for lista de listas (caso de fetch_projecoes_historico), achatar
    if dados and isinstance(dados[0], list):
        dados = [item for sublist in dados for item in sublist]
    
    # Filtrar apenas dicionários válidos
    registros = [item for item in dados if isinstance(item, dict)]
    
    if not registros:
        return pd.DataFrame()
    
    return pd.DataFrame.from_records(registros)


