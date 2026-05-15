"""
Validação de dados brutos da API ANBIMA.
"""

from __future__ import annotations

import pandas as pd


def validate_mercado_secundario(df: pd.DataFrame) -> bool:
    """
    Valida se o DataFrame de mercado secundário tem estrutura esperada.
    
    Args:
        df: DataFrame a validar
        
    Returns:
        True se válido, False caso contrário
    """
    if df is None or df.empty:
        return False
    
    # Validações básicas podem ser adicionadas aqui
    # Por exemplo: verificar se colunas esperadas existem
    
    return True
