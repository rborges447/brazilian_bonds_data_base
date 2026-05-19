from __future__ import annotations

import re

import pandas as pd

from pipelines.silver.mappers.anbima_projecoes import projecoes_to_df
from pipelines.silver.normalize import normalize_date_columns, normalize_numeric_columns
from pipelines.silver.schemas import PROJECOES_NUMERIC, PROJECOES_RENAME_MAP

_OUT_COLS = [
    "indice",
    "tipo_projecao",
    "data_coleta",
    "ref_month",
    "variacao_projetada",
    "data_validade",
]


def ref_month_to_iso(val: object) -> str | None:
    """MM/YYYY, MM-YYYY, or ISO date → YYYY-MM-01."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s[:7] + "-01"
    m = re.match(r"^(\d{1,2})[/-](\d{4})$", s)
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}-01"
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.isna(dt):
            return None
        return f"{dt.year:04d}-{dt.month:02d}-01"
    except Exception:
        return None


def normalize_from_records(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=_OUT_COLS)

    df = projecoes_to_df(records)
    if df.empty:
        return pd.DataFrame(columns=_OUT_COLS)

    df = df.rename(columns=PROJECOES_RENAME_MAP)
    df = normalize_date_columns(df, ["data_coleta", "data_validade"])
    df = normalize_numeric_columns(df, PROJECOES_NUMERIC, use_comma_decimal=False)

    for col in ("indice", "tipo_projecao"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    if "ref_month" in df.columns:
        df["ref_month"] = df["ref_month"].map(ref_month_to_iso)
    elif "mes_referencia" in df.columns:
        df["ref_month"] = df["mes_referencia"].map(ref_month_to_iso)
        df = df.drop(columns=["mes_referencia"], errors="ignore")

    for c in _OUT_COLS:
        if c not in df.columns:
            df[c] = None
    return df[_OUT_COLS]


def normalize_partition(
    df_raw: pd.DataFrame,
    partition_value: str,
    dates: list[str] | None = None,
) -> pd.DataFrame:
    del partition_value, dates
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=_OUT_COLS)

    if "mes_referencia" in df_raw.columns or "ref_month" in df_raw.columns:
        df = df_raw.copy()
        if "mes_referencia" in df.columns and "ref_month" not in df.columns:
            df = df.rename(columns=PROJECOES_RENAME_MAP)
        return normalize_from_records(df.to_dict(orient="records"))

    records = df_raw.to_dict(orient="records")
    return normalize_from_records(records)
