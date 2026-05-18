from __future__ import annotations

from pathlib import Path

from rf_lake.settings import BRONZE_ROOT, SILVER_ROOT


def segment_key(dates: list[str]) -> str:
    if not dates:
        return "all"
    return f"{min(dates)}__{max(dates)}"


def bronze_parquet(dataset: str, dates: list[str]) -> Path:
    return BRONZE_ROOT / dataset / f"{segment_key(dates)}.parquet"


def bronze_json(dataset: str, dates: list[str]) -> Path:
    return BRONZE_ROOT / dataset / f"{segment_key(dates)}.json"


def silver_parquet(dataset: str, dates: list[str]) -> Path:
    return SILVER_ROOT / dataset / f"{segment_key(dates)}.parquet"
