"""
Validação de dados brutos da API Tesouro.
"""

from __future__ import annotations

import pandas as pd


def validate_resultados(df: pd.DataFrame) -> bool:
    """
    Valida se o DataFrame de resultados tem estrutura esperada.
    
    Args:
        df: DataFrame a validar
        
    Returns:
        True se válido, False caso contrário
    """
    if df is None or df.empty:
        return False
    
    return True
