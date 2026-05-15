"""
Validação de dados brutos da API BCB.
"""

from __future__ import annotations

import pandas as pd


def validate_negociacoes(df: pd.DataFrame) -> bool:
    """
    Valida se o DataFrame de negociações tem estrutura esperada.
    
    Args:
        df: DataFrame a validar
        
    Returns:
        True se válido, False caso contrário
    """
    if df is None or df.empty:
        return False
    
    # Validações básicas podem ser adicionadas aqui
    
    return True
