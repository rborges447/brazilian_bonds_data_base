"""
Funções de normalização comuns para ETL.

Normalizações reutilizáveis aplicadas a múltiplos datasets.
"""

from __future__ import annotations

from datetime import date, datetime
import pandas as pd


def normalize_numeric_columns(df: pd.DataFrame, columns: list[str], use_comma_decimal: bool = False) -> pd.DataFrame:
    """
    Normaliza colunas numéricas, tratando formato brasileiro se necessário.
    
    Args:
        df: DataFrame a normalizar
        columns: Lista de nomes de colunas numéricas
        use_comma_decimal: Se True, trata vírgula como separador decimal
        
    Returns:
        DataFrame com colunas numéricas normalizadas
    """
    df = df.copy()
    
    for col in columns:
        if col in df.columns:
            if use_comma_decimal:
                # Converte para string, substitui vírgula por ponto, depois converte para numérico
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def normalize_date_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Normaliza colunas de data para formato ISO (YYYY-MM-DD).
    
    Suporta múltiplos formatos de entrada:
    - DD/MM/YYYY (formato brasileiro) - PRIORIDADE
    - YYYY-MM-DD (formato ISO)
    - MM/DD/YYYY (formato americano)
    
    Args:
        df: DataFrame a normalizar
        columns: Lista de nomes de colunas de data
        
    Returns:
        DataFrame com colunas de data normalizadas (None para valores inválidos)
    """
    df = df.copy()
    
    for col in columns:
        if col not in df.columns:
            continue
        
        # Função auxiliar para converter uma data
        def convert_date(val):
            # Tratar valores None/NaN
            if pd.isna(val):
                return None

            # Fast-path: já é um tipo de data/hora (evita warnings e parsing ambíguo)
            if isinstance(val, (datetime, date, pd.Timestamp)):
                try:
                    dt = pd.Timestamp(val)
                except Exception:
                    return None
                if pd.isna(dt):
                    return None
                return dt.strftime("%Y-%m-%d")
            
            val_str = str(val).strip()
            
            # Tratar strings vazias ou inválidas
            if not val_str or val_str.lower() in ('nan', 'nat', 'none', '', 'none'):
                return None

            # Fast-path: 'YYYY-MM-DD' (ou 'YYYY-MM-DD ...') -> pega só a parte da data
            if len(val_str) >= 10 and val_str[4] == "-" and val_str[7] == "-":
                head = val_str[:10]
                try:
                    dt = datetime.strptime(head, "%Y-%m-%d")
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass
            
            # Tentar formatos em ordem de prioridade (DD/MM/YYYY primeiro)
            formats = [
                '%d/%m/%Y',      # DD/MM/YYYY (brasileiro) - PRIORIDADE
                '%Y-%m-%d',      # YYYY-MM-DD (ISO)
                '%m/%d/%Y',      # MM/DD/YYYY (americano)
                '%d-%m-%Y',      # DD-MM-YYYY
                '%Y/%m/%d',      # YYYY/MM/DD
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(val_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Se nenhum formato funcionou, tentar pd.to_datetime com dayfirst=True (DD/MM/YYYY)
            try:
                dt = pd.to_datetime(val_str, dayfirst=True, errors='coerce')
                if pd.isna(dt):
                    return None
                return dt.strftime('%Y-%m-%d')
            except Exception:
                return None
        
        # Aplicar conversão
        df[col] = df[col].apply(convert_date)
        
        # Garantir que valores inválidos sejam None (não strings)
        df[col] = df[col].replace('None', None)
        df[col] = df[col].replace('nan', None)
        df[col] = df[col].replace('NaT', None)
        df[col] = df[col].replace('', None)
    
    return df


def remove_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove colunas duplicadas do DataFrame.
    
    Args:
        df: DataFrame a limpar
        
    Returns:
        DataFrame sem colunas duplicadas
    """
    return df.loc[:, ~df.columns.duplicated()]
