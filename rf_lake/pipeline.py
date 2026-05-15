"""
Orquestrador: compõe Bronze → Silver → Gold por dataset.
"""

from __future__ import annotations

from rf_lake.bronze import run_bronze
from rf_lake.datasets import get_dataset_config
from rf_lake.gold import run_gold
from rf_lake.silver import run_silver


def run_dataset(name: str, candidate_dates: list[str], end_date: str | None = None) -> dict:
    """Executa as três camadas em sequência para um dataset."""
    from datetime import date

    if end_date is None:
        end_date = date.today().isoformat()

    cfg = get_dataset_config(name)
    bronze = run_bronze(name, candidate_dates)
    if bronze.status == "error" or bronze.path is None:
        return {
            "raw_rows": 0,
            "transformed_rows": 0,
            "persisted": False,
            "bronze": bronze.status,
            "silver": "skipped",
            "gold": "skipped",
            "error": bronze.error,
        }

    silver = run_silver(name, bronze.path, candidate_dates)
    if silver.status == "error" or silver.path is None:
        return {
            "raw_rows": bronze.raw_rows,
            "transformed_rows": 0,
            "persisted": False,
            "bronze": bronze.status,
            "silver": silver.status,
            "gold": "skipped",
            "error": silver.error,
        }

    gold = run_gold(name, [silver.path], candidate_dates, end_date, config=cfg)
    return {
        "raw_rows": bronze.raw_rows,
        "transformed_rows": silver.rows,
        "persisted": gold.persisted,
        "bronze": bronze.status,
        "silver": silver.status,
        "gold": gold.status,
        "dates_bronze": bronze.dates_processed,
        "dates_silver": silver.dates_processed,
        "dates_gold": gold.dates_loaded,
    }


def run_pipeline(name: str, dates: list[str]) -> dict:
    """Alias de compatibilidade para backfill / run_one."""
    return run_dataset(name, dates)
