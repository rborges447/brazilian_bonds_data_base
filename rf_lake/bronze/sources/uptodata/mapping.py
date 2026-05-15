"""
Mapeamento de dados UpToData para formato canônico.
"""

from __future__ import annotations

import pandas as pd


def filtro_DI_DAP(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra DataFrame para manter apenas contratos DI/DAP.
    
    Args:
        df: DataFrame com dados de ajustes BMF
        
    Returns:
        DataFrame filtrado
    """
    if df is None or df.empty or 'TckrSymb' not in df.columns:
        return df
    
    return df[df['TckrSymb'].str.startswith(('DAP', 'DI1'))]


def map_ajustes_bmf_to_canonical(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Mapeia DataFrame bruto do UpToData para formato canônico.
    
    Args:
        df_raw: DataFrame bruto do UpToData
        
    Returns:
        DataFrame no formato canônico
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()
    
    # Aplica filtro DI/DAP
    df = filtro_DI_DAP(df_raw.copy())
    
    return df
