"""
Leitura e preview de dados por camada (Bronze / Silver / Gold) em um intervalo de datas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pandas as pd

from rf_lake.datasets import DATASETS
from rf_lake.gold.db import get_conn
from rf_lake.gold.db.queries import (
    get_ajustes_bmf,
    get_feriados,
    get_ipca_indice,
    get_leiloes,
    get_liquidacoes_mercado,
    get_mercado_secundario,
    get_projecoes,
    list_dates,
)
from rf_lake.date_fields import (
    BRONZE_DATE_COL,
    SILVER_DATE_COL,
    filter_df_by_iso_dates,
    pick_date_column,
)
from rf_lake.incremental import is_snapshot_dataset, silver_paths_for_dataset
from rf_lake.settings import BRONZE_ROOT, SILVER_ROOT


def business_dates(start_date: str, end_date: str) -> list[str]:
    """Dias úteis entre start e end (inclusive)."""
    return list_dates(start_date, end_date=end_date, skip_weekends=True)


def _artifact_paths_in_range(layer_root: Path, dataset: str, dates: list[str]) -> list[Path]:
    """Parquets/json cujo segmento intersecta o conjunto de datas."""
    if is_snapshot_dataset(dataset):
        dataset_dir = layer_root / dataset
        if not dataset_dir.is_dir():
            return []
        out: list[Path] = []
        for pattern in ("*snapshot*.parquet", "*snapshot*.json"):
            out.extend(sorted(dataset_dir.glob(pattern)))
        return out

    paths = silver_paths_for_dataset(dataset, dates)
    if layer_root == BRONZE_ROOT and dataset == "projecoes":
        dataset_dir = BRONZE_ROOT / dataset
        if dataset_dir.is_dir():
            for p in sorted(dataset_dir.glob("*.json")):
                if p not in paths:
                    paths.append(p)
    return paths


def _read_parquet_paths(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in paths:
        if not path.is_file() or path.stat().st_size == 0:
            continue
        if path.suffix == ".json":
            with path.open(encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, list):
                frames.append(pd.json_normalize(payload) if payload else pd.DataFrame())
            else:
                frames.append(pd.DataFrame([payload]))
        else:
            frames.append(pd.read_parquet(path))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def read_bronze_range(dataset: str, start_date: str, end_date: str) -> pd.DataFrame:
    dates = business_dates(start_date, end_date)
    paths = _artifact_paths_in_range(BRONZE_ROOT, dataset, dates)
    df = _read_parquet_paths(paths)
    if df.empty:
        return df
    col = pick_date_column(df, BRONZE_DATE_COL.get(dataset, []))
    if col is None and dataset in SILVER_DATE_COL and SILVER_DATE_COL[dataset]:
        col = SILVER_DATE_COL[dataset]
    return filter_df_by_iso_dates(df, col, start_date, end_date)


def read_silver_range(dataset: str, start_date: str, end_date: str) -> pd.DataFrame:
    dates = business_dates(start_date, end_date)
    paths = _artifact_paths_in_range(SILVER_ROOT, dataset, dates)
    df = _read_parquet_paths(paths)
    if df.empty:
        return df
    col = SILVER_DATE_COL.get(dataset)
    return filter_df_by_iso_dates(df, col, start_date, end_date)


def read_gold_range(dataset: str, start_date: str, end_date: str) -> pd.DataFrame:
    if dataset not in DATASETS:
        raise ValueError(f"Dataset desconhecido: {dataset}")

    conn = get_conn()
    try:
        if dataset == "mercado_secundario":
            return get_mercado_secundario(
                conn, start_date=start_date, end_date=end_date
            )
        if dataset == "liquidacoes_mercado":
            return get_liquidacoes_mercado(
                conn, start_date=start_date, end_date=end_date
            )
        if dataset == "ajustes_bmf":
            return get_ajustes_bmf(conn, start_date=start_date, end_date=end_date)
        if dataset == "leiloes":
            return get_leiloes(conn, start_date=start_date, end_date=end_date)
        if dataset == "feriados":
            df = get_feriados(conn)
            return filter_df_by_iso_dates(df, "data", start_date, end_date)
        if dataset == "ipca_indice":
            return get_ipca_indice(
                conn, start_month=f"{start_date[:7]}-01", end_month=f"{end_date[:7]}-01"
            )
        if dataset == "projecoes":
            return get_projecoes(
                conn,
                start_data_coleta=start_date,
                end_data_coleta=end_date,
            )
        return pd.DataFrame()
    finally:
        conn.close()


LAYER_READERS: dict[str, Callable[[str, str, str], pd.DataFrame]] = {
    "bronze": read_bronze_range,
    "silver": read_silver_range,
    "gold": read_gold_range,
}


def read_layer_range(layer: str, dataset: str, start_date: str, end_date: str) -> pd.DataFrame:
    reader = LAYER_READERS.get(layer)
    if reader is None:
        raise ValueError(f"Camada desconhecida: {layer}")
    return reader(dataset, start_date, end_date)


def format_layer_report(
    layer: str,
    dataset: str,
    df: pd.DataFrame,
    *,
    start_date: str,
    end_date: str,
    head_rows: int = 5,
) -> str:
    lines = [
        "",
        "=" * 72,
        f"  {layer.upper()} | {dataset} | {start_date} .. {end_date}",
        f"  shape: {df.shape[0]} rows x {df.shape[1]} cols",
        "=" * 72,
        "",
        "--- head() ---",
        df.head(head_rows).to_string() if not df.empty else "(vazio)",
        "",
        "--- dtypes ---",
        df.dtypes.to_string() if not df.empty else "(vazio)",
        "",
    ]
    return "\n".join(lines)


def all_layers_summary(
    start_date: str,
    end_date: str,
    datasets: list[str] | None = None,
) -> pd.DataFrame:
    """Tabela resumo (dataset, layer, rows, cols)."""
    names = datasets or list(DATASETS.keys())
    rows: list[dict] = []
    for dataset in names:
        for layer in ("bronze", "silver", "gold"):
            try:
                df = read_layer_range(layer, dataset, start_date, end_date)
                rows.append(
                    {
                        "dataset": dataset,
                        "layer": layer,
                        "rows": len(df),
                        "cols": len(df.columns),
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "dataset": dataset,
                        "layer": layer,
                        "rows": -1,
                        "cols": -1,
                        "error": str(exc),
                    }
                )
    return pd.DataFrame(rows)
