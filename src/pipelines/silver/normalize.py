"""Shared normalization helpers for silver ETL (port of legacy rf_lake.silver.normalize)."""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd


def normalize_numeric_columns(
    df: pd.DataFrame, columns: list[str], use_comma_decimal: bool = False
) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            if use_comma_decimal:
                df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def normalize_date_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()

    def convert_date(val: object) -> str | None:
        if pd.isna(val):
            return None
        if isinstance(val, (datetime, date, pd.Timestamp)):
            try:
                dt = pd.Timestamp(val)
            except Exception:
                return None
            if pd.isna(dt):
                return None
            return dt.strftime("%Y-%m-%d")

        val_str = str(val).strip()
        if not val_str or val_str.lower() in ("nan", "nat", "none", ""):
            return None

        if len(val_str) >= 10 and val_str[4] == "-" and val_str[7] == "-":
            head = val_str[:10]
            try:
                return datetime.strptime(head, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                pass

        formats = ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return datetime.strptime(val_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

        try:
            dt = pd.to_datetime(val_str, dayfirst=True, errors="coerce")
            if pd.isna(dt):
                return None
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None

    for col in columns:
        if col not in df.columns:
            continue
        df[col] = df[col].apply(convert_date)
        for bad in ("None", "nan", "NaT", ""):
            df[col] = df[col].replace(bad, None)

    return df


def remove_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.duplicated()]
