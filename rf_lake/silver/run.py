"""
Silver: reads Bronze, validates and normalizes, writes canonical Parquet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from rf_lake.bronze.paths import silver_parquet
from rf_lake.date_fields import dates_present_in_dataframe


def _write_silver(path: Path, df: pd.DataFrame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    return path


def _write_silver_series(
    dataset: str,
    df: pd.DataFrame | None,
) -> tuple[Path | None, int, list[str]]:
    frame = df if df is not None else pd.DataFrame()
    if frame.empty:
        return None, 0, []
    dates_with_data = dates_present_in_dataframe(frame, dataset, layer="silver")
    if not dates_with_data:
        return None, 0, []
    path = silver_parquet(dataset, dates_with_data)
    _write_silver(path, frame)
    return path, int(len(frame)), dates_with_data


def silver_mercado_secundario(bronze_path: Path, dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.anbima.validators import validate_mercado_secundario
    from rf_lake.silver.transforms.mercado_secundario import normalize as norm

    df_raw = pd.read_parquet(bronze_path)
    if df_raw.empty or not validate_mercado_secundario(df_raw):
        return None, 0, []
    df = norm(df_raw, dates=dates)
    return _write_silver_series("mercado_secundario", df)


def silver_liquidacoes_mercado(bronze_path: Path, dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.bcb.validators import validate_negociacoes
    from rf_lake.silver.transforms.liquidacoes_mercado import normalize as norm

    df_raw = pd.read_parquet(bronze_path)
    if df_raw.empty or not validate_negociacoes(df_raw):
        return None, 0, []
    df = norm(df_raw, dates=dates)
    return _write_silver_series("liquidacoes_mercado", df)


def silver_ajustes_bmf(bronze_path: Path, dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.uptodata.validators import validate_ajustes_bmf
    from rf_lake.silver.transforms.ajustes_bmf import normalize as norm

    df_raw = pd.read_parquet(bronze_path)
    if df_raw.empty or not validate_ajustes_bmf(df_raw):
        return None, 0, []
    df = norm(df_raw, dates=dates)
    return _write_silver_series("ajustes_bmf", df)


def silver_leiloes(bronze_path: Path, dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.tesouro.validators import validate_resultados
    from rf_lake.silver.transforms.leiloes import normalize as norm

    df_raw = pd.read_parquet(bronze_path)
    if df_raw.empty or not validate_resultados(df_raw):
        return None, 0, []
    df = norm(df_raw, dates=dates)
    return _write_silver_series("leiloes", df)


def silver_ipca_indice(bronze_path: Path, dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.sidra.mapping import sidra_ipca_to_long
    from rf_lake.bronze.sources.sidra.validators import validate_ipca_long
    from rf_lake.silver.transforms.ipca_indice import ipca_long_to_monthly

    df_sidra = pd.read_parquet(bronze_path)
    if df_sidra.empty:
        return None, 0, []
    df_long = sidra_ipca_to_long(df_sidra)
    if df_long.empty or not validate_ipca_long(df_long):
        return None, 0, []
    df_monthly = ipca_long_to_monthly(df_long)
    if df_monthly is None or df_monthly.empty:
        return None, 0, []
    path = silver_parquet("ipca_indice", dates if dates else ["snapshot"])
    _write_silver(path, df_monthly)
    return path, int(len(df_monthly)), ["snapshot"]


def silver_projecoes(bronze_json_path: Path, dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.anbima.mapping import projecoes_to_df
    from rf_lake.silver.transforms.projecoes import normalize as norm

    with bronze_json_path.open(encoding="utf-8") as f:
        payloads = json.load(f)
    df_raw = projecoes_to_df(payloads)
    if df_raw.empty:
        return None, 0, []
    df = norm(df_raw)
    path = silver_parquet("projecoes", dates if dates else ["snapshot"])
    _write_silver(path, df)
    return path, int(len(df)), dates if dates else ["snapshot"]


def silver_feriados(bronze_path: Path, dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.silver.transforms.feriados import normalize as norm

    df_raw = pd.read_parquet(bronze_path)
    df = norm(df_raw)
    if df.empty:
        return None, 0, []
    path = silver_parquet("feriados", dates if dates else ["snapshot"])
    _write_silver(path, df)
    return path, int(len(df)), ["snapshot"]


SILVER_FUNCS = {
    "mercado_secundario": silver_mercado_secundario,
    "liquidacoes_mercado": silver_liquidacoes_mercado,
    "ajustes_bmf": silver_ajustes_bmf,
    "leiloes": silver_leiloes,
    "ipca_indice": silver_ipca_indice,
    "projecoes": silver_projecoes,
    "feriados": silver_feriados,
}


def silver_from_bronze(name: str, bronzep: Path, dates: list[str]) -> tuple[Path | None, int, list[str]]:
    return SILVER_FUNCS[name](bronzep, dates)
