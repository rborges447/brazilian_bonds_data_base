"""Date columns per dataset and helpers for ISO normalization."""

from __future__ import annotations

import pandas as pd

SILVER_DATE_COL: dict[str, str | None] = {
    "mercado_secundario": "data_referencia",
    "liquidacoes_mercado": "data_referencia",
    "ajustes_bmf": "data_referencia",
    "leiloes": "data_referencia",
    "feriados": "data",
    "ipca_indice": "ref_month",
    "projecoes": "data_coleta",
}

BRONZE_DATE_COL: dict[str, list[str]] = {
    "mercado_secundario": ["data_referencia", "dataReferencia"],
    "liquidacoes_mercado": ["data_referencia", "DATA MOV", "data_mov"],
    "ajustes_bmf": ["data_referencia", "RptDt"],
    "leiloes": ["data_referencia", "data_leilao"],
    "feriados": ["data"],
    "ipca_indice": ["ref_month", "DATA", "DATA_CODIGO"],
    "projecoes": ["data_coleta"],
}


def pick_date_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def date_candidates_for_layer(dataset: str, layer: str) -> list[str]:
    if layer == "silver":
        col = SILVER_DATE_COL.get(dataset)
        return [col] if col else []
    return list(BRONZE_DATE_COL.get(dataset, []))


def _to_iso_date_string(val: object) -> str | None:
    """Normalize a date value to YYYY-MM-DD."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()[:10]
    s = str(val).strip()
    if not s or s.lower() in ("nan", "nat", "none"):
        return None
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    if len(s) >= 10 and s[2] == "/" and s[5] == "/":
        from datetime import datetime as dt

        try:
            return dt.strptime(s[:10], "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None


def normalize_date_series(series: pd.Series, date_col: str) -> set[str]:
    """Convert a date column to a set of ISO YYYY-MM-DD strings."""
    if series.empty:
        return set()
    if date_col == "ref_month":
        as_str = series.apply(
            lambda x: x.isoformat()[:10] if hasattr(x, "isoformat") else str(x)[:10]
        )
        out: set[str] = set()
        for val in as_str.dropna().unique():
            s = str(val).strip()
            if len(s) >= 10 and s[4] == "-" and s[7] == "-":
                out.add(s[:10])
        return out
    out = set()
    for val in series.dropna().unique():
        iso = _to_iso_date_string(val)
        if iso:
            out.add(iso)
    return out


def distinct_dates_in_df(df: pd.DataFrame, date_col_candidates: list[str]) -> list[str]:
    """Distinct dates present in the DataFrame (sorted)."""
    if df.empty or not date_col_candidates:
        return []
    col = pick_date_column(df, date_col_candidates)
    if col is None:
        return []
    return sorted(normalize_date_series(df[col], col))


def dates_present_in_dataframe(
    df: pd.DataFrame, dataset: str, layer: str = "bronze"
) -> list[str]:
    """Distinct dates in the DataFrame for segment_key / watermark."""
    candidates = date_candidates_for_layer(dataset, layer)
    return distinct_dates_in_df(df, candidates)


def filter_df_by_iso_dates(
    df: pd.DataFrame,
    date_col: str | None,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    if df.empty or date_col is None or date_col not in df.columns:
        return df

    series = df[date_col]
    if date_col == "ref_month" and series.dtype == object:
        as_str = series.apply(
            lambda x: x.isoformat()[:10] if hasattr(x, "isoformat") else str(x)[:10]
        )
        mask = (as_str >= start_date) & (as_str <= end_date)
        return df.loc[mask].copy()

    as_str = series.astype(str).str[:10]
    mask = (as_str >= start_date) & (as_str <= end_date)
    return df.loc[mask].copy()
