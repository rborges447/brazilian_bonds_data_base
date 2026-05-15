"""
Shared normalization helpers for ETL.

Reusable transforms applied across datasets.
"""

from __future__ import annotations

from datetime import date, datetime
import pandas as pd


def normalize_numeric_columns(df: pd.DataFrame, columns: list[str], use_comma_decimal: bool = False) -> pd.DataFrame:
    """
    Normalize numeric columns, optionally handling Brazilian formatting.

    Args:
        df: Input DataFrame
        columns: Numeric column names
        use_comma_decimal: If True, treat comma as decimal separator

    Returns:
        DataFrame with numeric columns coerced
    """
    df = df.copy()
    
    for col in columns:
        if col in df.columns:
            if use_comma_decimal:
                # Stringify, replace comma with dot, then coerce numeric
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def normalize_date_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Normalize date columns to ISO (YYYY-MM-DD).

    Supported inputs:
    - DD/MM/YYYY (Brazilian) — tried first
    - YYYY-MM-DD (ISO)
    - MM/DD/YYYY (US)

    Args:
        df: Input DataFrame
        columns: Date column names

    Returns:
        DataFrame with dates as strings or None for invalid values
    """
    df = df.copy()
    
    for col in columns:
        if col not in df.columns:
            continue
        
        # Helper to convert one cell
        def convert_date(val):
            # Handle None/NaN
            if pd.isna(val):
                return None

            # Fast-path: already a datetime-like type (avoids ambiguous parsing warnings)
            if isinstance(val, (datetime, date, pd.Timestamp)):
                try:
                    dt = pd.Timestamp(val)
                except Exception:
                    return None
                if pd.isna(dt):
                    return None
                return dt.strftime("%Y-%m-%d")
            
            val_str = str(val).strip()
            
            # Handle empty or invalid strings
            if not val_str or val_str.lower() in ('nan', 'nat', 'none', '', 'none'):
                return None

            # Fast-path: 'YYYY-MM-DD' (or 'YYYY-MM-DD ...') — take date portion only
            if len(val_str) >= 10 and val_str[4] == "-" and val_str[7] == "-":
                head = val_str[:10]
                try:
                    dt = datetime.strptime(head, "%Y-%m-%d")
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass
            
            # Try formats in priority order (DD/MM/YYYY first)
            formats = [
                '%d/%m/%Y',      # DD/MM/YYYY (Brazilian) — priority
                '%Y-%m-%d',      # YYYY-MM-DD (ISO)
                '%m/%d/%Y',      # MM/DD/YYYY (US)
                '%d-%m-%Y',      # DD-MM-YYYY
                '%Y/%m/%d',      # YYYY/MM/DD
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(val_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Fallback: pandas with dayfirst=True (DD/MM/YYYY)
            try:
                dt = pd.to_datetime(val_str, dayfirst=True, errors='coerce')
                if pd.isna(dt):
                    return None
                return dt.strftime('%Y-%m-%d')
            except Exception:
                return None
        
        # Apply conversion
        df[col] = df[col].apply(convert_date)
        
        # Normalize invalid values to None (not string placeholders)
        df[col] = df[col].replace('None', None)
        df[col] = df[col].replace('nan', None)
        df[col] = df[col].replace('NaT', None)
        df[col] = df[col].replace('', None)
    
    return df


def remove_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop duplicate column names from the DataFrame.

    Args:
        df: DataFrame to clean

    Returns:
        DataFrame without duplicate columns
    """
    return df.loc[:, ~df.columns.duplicated()]
