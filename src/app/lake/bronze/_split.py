"""Date helpers for hive partitioning only (no canonical schema)."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

import pandas as pd


def pick_date_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    for col in df.columns:
        stripped = col.strip()
        if stripped in candidates:
            return col
    return None


def to_iso_date_string(val: object) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if hasattr(val, "isoformat") and not isinstance(val, (int, float)):
        return val.isoformat()[:10]
    if isinstance(val, (int, float)) and not pd.isna(val):
        try:
            code = int(val)
            s = f"{code:06d}"
            if len(s) == 6 and s.isdigit():
                return f"{s[:4]}-{s[4:6]}-01"
        except (ValueError, OverflowError):
            return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "nat", "none"):
        return None
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    if len(s) >= 10 and s[2] == "/" and s[5] == "/":
        try:
            return datetime.strptime(s[:10], "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return None
    if "." in s:
        try:
            code = int(float(s))
            s = f"{code:06d}"
        except (ValueError, OverflowError):
            return None
    if len(s) == 6 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-01"
    return None


def partition_values_from_series(series: pd.Series, granularity: str) -> list[str]:
    values: set[str] = set()
    for raw in series.dropna().unique():
        iso = to_iso_date_string(raw)
        if not iso:
            continue
        if granularity == "month":
            values.add(iso[:7] + "-01")
        else:
            values.add(iso)
    return sorted(values)


def split_dataframe_by_partition(
    df: pd.DataFrame,
    date_col: str,
    granularity: str,
) -> dict[str, pd.DataFrame]:
    if df.empty or date_col not in df.columns:
        return {}
    iso_series = df[date_col].map(to_iso_date_string)
    if granularity == "month":
        part_series = iso_series.map(
            lambda x: f"{x[:7]}-01" if isinstance(x, str) and len(x) >= 7 else None
        )
    else:
        part_series = iso_series
    out: dict[str, pd.DataFrame] = {}
    for part_val in sorted(v for v in part_series.dropna().unique() if v):
        chunk = df.loc[part_series == part_val].copy()
        if not chunk.empty:
            out[str(part_val)] = chunk
    return out


def iso_month_from_mes_ano(mes: int | str, ano: int | str) -> str:
    from app.core.dates import iso_month_first

    return iso_month_first(int(ano), int(mes))


def months_from_candidate_dates(dates: list[str]) -> list[str]:
    months: set[str] = set()
    for d in dates:
        s = str(d).strip()
        if len(s) >= 7 and s[4] == "-":
            months.add(s[:7] + "-01")
        elif len(s) >= 10:
            months.add(s[:7] + "-01")
    return sorted(months)


def auction_date_from_record(record: dict) -> str | None:
    for key in ("dataLeilao", "data_leilao", "data_referencia", "dataleilao"):
        if key in record:
            return to_iso_date_string(record[key])
    return None
