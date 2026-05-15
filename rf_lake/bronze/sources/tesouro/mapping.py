"""
Mapeamento de dados da API Tesouro para formato canônico.
"""

from __future__ import annotations

import pandas as pd


def map_tesouro_to_canonical(data: list) -> pd.DataFrame:
    """
    Mapeia lista de resultados para DataFrame canônico.
    
    Args:
        data: Lista de dicionários de resultados
        
    Returns:
        DataFrame no formato canônico
    """
    if not data:
        return pd.DataFrame()
    
    # Filtra apenas dicionários válidos (não None e não vazios)
    valid_records = [
        record for record in data 
        if isinstance(record, dict) and record
    ]
    
    if not valid_records:
        return pd.DataFrame()
    
    # Converte lista de dicionários em DataFrame
    df = pd.DataFrame.from_records(valid_records)
    
    return df
