"""Silver: ANBIMA VNA (explode titulos[] to one row per title)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.lake.silver.normalize import normalize_date_columns, normalize_numeric_columns
from app.lake.silver.schemas import VNA_NUMERIC, VNA_RENAME_MAP

_OUT_COLS = [
    "data_referencia",
    "codigo_selic",
    "tipo_correcao",
    "index",
    "data_validade",
    "vna",
]

_DATA_ALIASES = ("data_referencia", "data", "Data", "dt_referencia")
_TITULOS_ALIASES = ("titulos", "Titulos", "itens")


def _pick_field(record: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        if key in record and record[key] is not None:
            return record[key]
    return None


def _coerce_records(records: list[dict] | dict | None) -> list[dict]:
    if records is None:
        return []
    if isinstance(records, dict):
        return [records]
    return [item for item in records if isinstance(item, dict)]


def _explode_day_records(records: list[dict]) -> list[dict]:
    flat: list[dict] = []
    for record in records:
        titulos = _pick_field(record, _TITULOS_ALIASES)
        if titulos is not None:
            data_ref = _pick_field(record, _DATA_ALIASES)
            if not isinstance(titulos, list):
                continue
            for titulo in titulos:
                if not isinstance(titulo, dict):
                    continue
                row = dict(titulo)
                if data_ref is not None and "data_referencia" not in row:
                    row["data_referencia"] = data_ref
                flat.append(row)
            continue

        if any(key in record for key in ("codigo_selic", "codigoSelic", "codigo", "cod_selic")):
            flat.append(record)
    return flat


def _empty_output() -> pd.DataFrame:
    return pd.DataFrame(columns=_OUT_COLS)


def normalize_from_records(records: list[dict] | dict | None) -> pd.DataFrame:
    coerced = _coerce_records(records)
    if not coerced:
        return _empty_output()

    flat = _explode_day_records(coerced)
    if not flat:
        return _empty_output()

    df = pd.DataFrame.from_records(flat)
    rename_map = {k: v for k, v in VNA_RENAME_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    df = normalize_date_columns(df, ["data_referencia", "data_validade"])
    df = normalize_numeric_columns(df, VNA_NUMERIC, use_comma_decimal=True)

    if "codigo_selic" in df.columns:
        df["codigo_selic"] = pd.to_numeric(df["codigo_selic"], errors="coerce").astype("Int64")

    if "tipo_correcao" in df.columns:
        df["tipo_correcao"] = df["tipo_correcao"].astype(str).str.strip()

    for col in ("data_referencia", "codigo_selic", "vna"):
        if col in df.columns:
            df = df[df[col].notna()].copy()

    df = df.drop_duplicates(subset=["data_referencia", "codigo_selic"], keep="last")

    for col in _OUT_COLS:
        if col not in df.columns:
            df[col] = None
    return df[_OUT_COLS].reset_index(drop=True)


def normalize_partition(
    df_raw: pd.DataFrame,
    partition_value: str,
    dates: list[str] | None = None,
) -> pd.DataFrame:
    if df_raw is None or df_raw.empty:
        return _empty_output()

    titulos_cols = [c for c in _TITULOS_ALIASES if c in df_raw.columns]
    if titulos_cols:
        df = normalize_from_records(df_raw.to_dict(orient="records"))
    elif "codigo_selic" in df_raw.columns or any(
        alias in df_raw.columns for alias in ("codigoSelic", "codigo", "cod_selic")
    ):
        df = normalize_from_records(df_raw.to_dict(orient="records"))
    else:
        return _empty_output()

    filter_dates = dates if dates is not None else ([partition_value] if partition_value else None)
    if filter_dates and "data_referencia" in df.columns:
        df = df[df["data_referencia"].isin(set(filter_dates))].copy()
    return df.reset_index(drop=True)
