"""
Extração Bronze: apenas busca e gravação de brutos (Parquet/JSON).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from rf_lake.bronze.paths import bronze_json, bronze_parquet
from rf_lake.date_fields import dates_present_in_dataframe


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _write_df(path: Path, df: pd.DataFrame | None) -> Path:
    _ensure_parent(path)
    out = df if df is not None else pd.DataFrame()
    out.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    return path


def _write_bronze_series(
    dataset: str,
    df: pd.DataFrame | None,
) -> tuple[Path | None, int, list[str]]:
    """
    Grava parquet só se houver linhas; segment_key = datas presentes no conteúdo.
  """
    frame = df if df is not None else pd.DataFrame()
    if frame.empty:
        return None, 0, []
    dates_with_data = dates_present_in_dataframe(frame, dataset, layer="bronze")
    if not dates_with_data:
        return None, 0, []
    path = bronze_parquet(dataset, dates_with_data)
    _write_df(path, frame)
    return path, int(len(frame)), dates_with_data


def extract_mercado_secundario(dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.anbima.client import AnbimaClient, MERCADO_SECUNDARIO_TPF
    from rf_lake.bronze.sources.anbima.mapping import api_list_to_df

    if not dates:
        return None, 0, []
    client = AnbimaClient()
    payloads = client.fetch_for_dates(MERCADO_SECUNDARIO_TPF, dates)
    df_raw = api_list_to_df(payloads)
    return _write_bronze_series("mercado_secundario", df_raw)


def extract_liquidacoes_mercado(dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.bcb.client import fetch_negociacoes_bruto_por_datas

    if not dates:
        return None, 0, []
    df_raw = fetch_negociacoes_bruto_por_datas(dates, date_column="DATA MOV")
    return _write_bronze_series("liquidacoes_mercado", df_raw)


def extract_ajustes_bmf(dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.uptodata.client import (
        ARQUIVO_INTEREST_RATE_BASE,
        PASTA_INTEREST_RATE_BASE,
        scrap_ajustes_bmf_for_dates,
    )

    if not dates:
        return None, 0, []
    df_interest = scrap_ajustes_bmf_for_dates(
        PASTA_INTEREST_RATE_BASE, ARQUIVO_INTEREST_RATE_BASE, dates
    )
    return _write_bronze_series("ajustes_bmf", df_interest)


def extract_leiloes(dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.tesouro.client import get_resultados_by_dates
    from rf_lake.bronze.sources.tesouro.mapping import map_tesouro_to_canonical

    if not dates:
        return None, 0, []
    all_resultados = get_resultados_by_dates(dates)
    df_raw = map_tesouro_to_canonical(all_resultados)
    return _write_bronze_series("leiloes", df_raw)


def extract_ipca_indice(dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.sidra.client import SidraIpcaClient

    path = bronze_parquet("ipca_indice", dates if dates else ["snapshot"])
    client = SidraIpcaClient()
    df_sidra = client.fetch_table_ipca()
    if df_sidra is None or df_sidra.empty:
        return None, 0, []
    _write_df(path, df_sidra)
    return path, int(len(df_sidra)), ["snapshot"]


def extract_projecoes(dates: list[str], payloads: list[Any]) -> tuple[Path | None, int, list[str]]:
    """Grava JSON com lista de respostas brutas (mesmo formato esperado por projecoes_to_df)."""
    if not payloads:
        return None, 0, []
    path = bronze_json("projecoes", dates if dates else ["snapshot"])
    _ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payloads, f, ensure_ascii=False, default=str)
    n = sum(len(x) if isinstance(x, list) else 1 for x in payloads)
    return path, int(n), dates if dates else ["snapshot"]


def extract_feriados(dates: list[str]) -> tuple[Path | None, int, list[str]]:
    from rf_lake.bronze.sources.feriados.client import fetch_feriados

    path = bronze_parquet("feriados", dates if dates else ["snapshot"])
    raw = fetch_feriados()
    if not raw:
        return None, 0, []
    df = pd.DataFrame({"data": raw})
    _write_df(path, df)
    return path, int(len(df)), ["snapshot"]


EXTRACTORS = {
    "mercado_secundario": extract_mercado_secundario,
    "liquidacoes_mercado": extract_liquidacoes_mercado,
    "ajustes_bmf": extract_ajustes_bmf,
    "leiloes": extract_leiloes,
    "ipca_indice": extract_ipca_indice,
    "feriados": extract_feriados,
}


def extract_dataset(name: str, dates: list[str]) -> tuple[Path | None, int, list[str]]:
    fn = EXTRACTORS.get(name)
    if fn is None:
        raise ValueError(f"Dataset sem extrator direto: {name} (use fluxo projecoes no job)")
    return fn(dates)
