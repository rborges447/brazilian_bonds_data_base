"""
Mapeamento de dados da API BCB para formato canônico.
"""

from __future__ import annotations

import pandas as pd


def map_negociacoes_to_canonical(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Mapeia DataFrame bruto do BCB para formato canônico.
    
    Args:
        df_raw: DataFrame bruto do BCB
        
    Returns:
        DataFrame no formato canônico
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()
    
    # Por enquanto retorna o DataFrame como está
    # O mapeamento específico será feito nos pipelines ETL
    return df_raw.copy()
