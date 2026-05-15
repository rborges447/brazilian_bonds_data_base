"""Resolução incremental de datas faltantes por camada (Bronze / Silver / Gold)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from rf_lake.bronze.paths import bronze_json, bronze_parquet, silver_parquet
from rf_lake.date_fields import (
    date_candidates_for_layer,
    normalize_date_series,
    pick_date_column,
)
from rf_lake.gold.db.queries import missing_dates_for_table
from rf_lake.settings import BRONZE_ROOT, DATA_START_DATE, SILVER_ROOT

if TYPE_CHECKING:
    from rf_lake.datasets import DatasetConfig

SNAPSHOT_DATASETS = frozenset({"feriados", "ipca_indice", "projecoes"})


def parse_segment_stem(stem: str) -> tuple[str, str] | None:
    """Interpreta stem de arquivo: 2026-01-02__2026-01-10, snapshot__snapshot, all."""
    if "__" not in stem:
        return None
    left, right = stem.split("__", 1)
    return left, right


def _expand_date_range(start: str, end: str, skip_weekends: bool = True) -> set[str]:
    try:
        start_dt = date.fromisoformat(start)
        end_dt = date.fromisoformat(end)
    except ValueError:
        return set()
    if start_dt > end_dt:
        return set()
    out: set[str] = set()
    cur = start_dt
    while cur <= end_dt:
        if (not skip_weekends) or cur.weekday() < 5:
            out.add(cur.isoformat())
        cur += timedelta(days=1)
    return out


def _dates_from_filename_stem(stem: str, *, skip_weekends: bool = True) -> set[str]:
    parsed = parse_segment_stem(stem)
    if parsed is None:
        return set()
    left, right = parsed
    if left == "snapshot" or right == "snapshot":
        return {"snapshot"}
    if left == "all" or right == "all":
        return set()
    return _expand_date_range(left, right, skip_weekends=skip_weekends)


def _read_date_column_from_parquet(path: Path, candidates: list[str]) -> tuple[set[str], bool]:
    """
    Retorna (datas presentes, coluna_encontrada).
    Se a coluna existe mas o arquivo está vazio, coluna_encontrada=True e datas vazias.
    """
    try:
        import pyarrow.parquet as pq

        schema = pq.read_schema(path)
        available = [c for c in candidates if c in schema.names]
        if not available:
            return set(), False
        table = pq.read_table(path, columns=available)
        df = table.to_pandas()
    except Exception:
        try:
            df = pd.read_parquet(path, columns=candidates)
        except Exception:
            df = pd.read_parquet(path)

    col = pick_date_column(df, candidates)
    if col is None:
        return set(), False
    if df.empty:
        return set(), True
    return normalize_date_series(df[col], col), True


def dates_present_in_dir(
    dataset_dir: Path,
    date_col_candidates: list[str],
    *,
    skip_weekends: bool = True,
) -> set[str]:
    """
    Datas efetivamente presentes nos parquets (coluna de negócio).
    Fallback: intervalo do nome do arquivo se nenhuma coluna for encontrada.
    """
    if not dataset_dir.is_dir() or not date_col_candidates:
        return set()

    present: set[str] = set()
    any_column_found = False

    for path in sorted(dataset_dir.glob("*.parquet")):
        if path.stat().st_size == 0:
            continue
        file_dates, has_col = _read_date_column_from_parquet(path, date_col_candidates)
        if has_col:
            any_column_found = True
            present |= file_dates
        else:
            present |= _dates_from_filename_stem(path.stem, skip_weekends=skip_weekends)

    if any_column_found:
        return present

    for path in sorted(dataset_dir.glob("*.parquet")) + sorted(dataset_dir.glob("*.json")):
        if path.stat().st_size == 0:
            continue
        present |= _dates_from_filename_stem(path.stem, skip_weekends=skip_weekends)
    return present


def dates_covered_in_dir(
    dataset_dir: Path,
    date_col_candidates: list[str] | None = None,
    *,
    skip_weekends: bool = True,
) -> set[str]:
    """Datas cobertas no diretório (por conteúdo quando possível)."""
    if date_col_candidates:
        return dates_present_in_dir(
            dataset_dir, date_col_candidates, skip_weekends=skip_weekends
        )
    if not dataset_dir.is_dir():
        return set()
    covered: set[str] = set()
    for path in list(dataset_dir.glob("*.parquet")) + list(dataset_dir.glob("*.json")):
        if path.stat().st_size == 0:
            continue
        covered |= _dates_from_filename_stem(path.stem, skip_weekends=skip_weekends)
    return covered


def missing_dates_subset(candidate: list[str], covered: set[str]) -> list[str]:
    """Preserva ordem; retorna só datas do candidato que não estão em covered."""
    if not candidate:
        return []
    return [d for d in candidate if d not in covered]


def _artifact_nonempty(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def snapshot_key_dates(dates: list[str]) -> list[str]:
    return dates if dates else ["snapshot"]


def is_snapshot_dataset(dataset: str) -> bool:
    return dataset in SNAPSHOT_DATASETS


def bronze_artifact_path(dataset: str, dates: list[str]) -> Path:
    key = snapshot_key_dates(dates)
    if dataset == "projecoes":
        return bronze_json(dataset, key)
    return bronze_parquet(dataset, key)


def missing_dates_bronze(dataset: str, candidate_dates: list[str]) -> list[str]:
    """Datas a extrair no raw (delta)."""
    if is_snapshot_dataset(dataset):
        key = snapshot_key_dates(candidate_dates)
        path = bronze_artifact_path(dataset, key)
        if _artifact_nonempty(path):
            return []
        return key

    candidates = date_candidates_for_layer(dataset, "bronze")
    covered = dates_covered_in_dir(BRONZE_ROOT / dataset, candidates)
    return missing_dates_subset(candidate_dates, covered)


def missing_dates_silver(
    dataset: str,
    candidate_dates: list[str],
    bronze_path: Path,
) -> list[str]:
    """Datas a transformar no silver (delta ou bronze mais novo)."""
    key = snapshot_key_dates(candidate_dates)

    if is_snapshot_dataset(dataset):
        silver_path = silver_parquet(dataset, key)
        if not _artifact_nonempty(silver_path):
            return key
        if bronze_path.is_file() and silver_path.is_file():
            if bronze_path.stat().st_mtime > silver_path.stat().st_mtime:
                return key
        return []

    candidates = date_candidates_for_layer(dataset, "silver")
    covered = dates_covered_in_dir(SILVER_ROOT / dataset, candidates)
    missing = missing_dates_subset(candidate_dates, covered)

    if not candidate_dates:
        return missing

    silver_path = silver_parquet(dataset, candidate_dates)
    if (
        silver_path.is_file()
        and bronze_path.is_file()
        and bronze_path.stat().st_mtime > silver_path.stat().st_mtime
    ):
        return candidate_dates

    return missing


def missing_dates_gold(config: DatasetConfig, end_date: str) -> list[str]:
    """Datas faltantes no SQLite (fonte de verdade de negócio)."""
    if config.date_mode == "missing_dates":
        if not config.table or not config.date_col:
            return []
        return missing_dates_for_table(
            table=config.table,
            date_col=config.date_col,
            default_start=config.start_if_empty or DATA_START_DATE,
            end_date=end_date,
            skip_weekends=True,
        )
    if is_snapshot_dataset(config.name):
        return ["snapshot"]
    return [end_date]


def silver_paths_for_dataset(dataset: str, candidate_dates: list[str]) -> list[Path]:
    """Lista parquets silver que contêm (no conteúdo) alguma data candidata."""
    dataset_dir = SILVER_ROOT / dataset
    if not dataset_dir.is_dir():
        return []

    if is_snapshot_dataset(dataset):
        p = silver_parquet(dataset, snapshot_key_dates(candidate_dates))
        return [p] if p.is_file() else []

    if not candidate_dates:
        return sorted(dataset_dir.glob("*.parquet"))

    needed = set(candidate_dates)
    candidates = date_candidates_for_layer(dataset, "silver")
    paths: list[Path] = []
    for path in sorted(dataset_dir.glob("*.parquet")):
        if path.stat().st_size == 0:
            continue
        if candidates:
            file_dates, has_col = _read_date_column_from_parquet(path, candidates)
            if not has_col:
                file_dates = _dates_from_filename_stem(path.stem)
        else:
            file_dates = _dates_from_filename_stem(path.stem)
        if file_dates & needed:
            paths.append(path)
    return paths
