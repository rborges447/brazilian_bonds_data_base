"""Read-only gap detection for bronze / silver / gold coverage."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import get_settings
from app.database.schema import TABLE_FERIADOS
from app.core.datasets import DATASETS
from app.core.partitioning import SNAPSHOT_VALUE, get_partition_spec, is_snapshot_dataset
from app.core.sync_range import (
    sync_business_days,
    sync_end_date,
    sync_ipca_months,
    sync_months,
    sync_start_date,
)
from app.lake.bronze.incremental import missing_partition_values
from app.lake.bronze.storage import partition_artifact_exists as bronze_exists
from app.lake.gold.contracts import BuilderName
from app.lake.gold.incremental import (
    BUILDER_TABLE,
    _dates_silver_ready,
    candidates_for_builder,
    missing_persisted_dates,
)
from app.lake.silver.incremental import missing_silver_partitions
from app.lake.silver.storage import partition_artifact_exists as silver_exists

MANDATORY_DATASETS: tuple[str, ...] = (
    "cdi",
    "ptax",
    "ipca_indice",
    "projecoes",
    "mercado_secundario",
    "liquidacoes_mercado",
    "feriados",
)

MANDATORY_BUILDERS: tuple[BuilderName, ...] = (
    "feriados",
    "cdi",
    "ptax",
    "ipca_dict",
    "bmf",
    "mercado_secundario",
    "liquidacoes_mercado",
)


def _dataset_candidates(dataset: str, start: str, end: str) -> list[str]:
    if is_snapshot_dataset(dataset):
        return []
    if dataset == "ipca_indice":
        return sync_ipca_months(end=end, start=start)
    if dataset == "projecoes":
        return sync_months(end=end, start=start)
    return sync_business_days(end=end, start=start)


def bronze_gaps(
    dataset: str,
    start: str | None = None,
    end: str | None = None,
) -> list[str]:
    """Partition values expected in bronze but missing."""
    range_start = sync_start_date(start)
    range_end = sync_end_date(end)
    candidates = _dataset_candidates(dataset, range_start, range_end)
    cfg = DATASETS.get(dataset)
    if cfg is None:
        raise ValueError(f"Unknown dataset: {dataset}")
    if cfg.date_mode == "missing_dates":
        return missing_partition_values(dataset, candidates)
    if dataset in ("ipca_indice", "projecoes", "feriados"):
        spec = get_partition_spec(dataset)
        if is_snapshot_dataset(dataset):
            val = SNAPSHOT_VALUE
            if bronze_exists(dataset, spec.partition_key, val, spec.artifact_ext):
                return []
            return [val]
        missing = [
            v
            for v in candidates
            if not bronze_exists(
                dataset, spec.partition_key, v, spec.artifact_ext
            )
        ]
        return missing
    return []


def silver_gaps(
    dataset: str,
    start: str | None = None,
    end: str | None = None,
) -> list[str]:
    """Bronze present, silver partition missing."""
    range_start = sync_start_date(start)
    range_end = sync_end_date(end)
    candidates = _dataset_candidates(dataset, range_start, range_end)
    return missing_silver_partitions(dataset, candidates)


def gold_gaps(
    builder: BuilderName,
    start: str | None = None,
    end: str | None = None,
    *,
    db_path: Any = None,
    check_persist: bool = True,
) -> list[str]:
    """Silver ready but gold row missing (when ``check_persist`` and DB exists)."""
    range_start = sync_start_date(start)
    range_end = sync_end_date(end)
    candidates = candidates_for_builder(builder, range_end, start=range_start)
    ready = _dates_silver_ready(builder, candidates)
    if not check_persist:
        return [d for d in candidates if d not in ready]
    meta = BUILDER_TABLE.get(builder)
    if meta is None or builder == "feriados":
        path = db_path or get_settings().db_path
        if builder == "feriados" and Path(path).is_file():
            from app.database.connection import get_connection

            conn = get_connection(db_path)
            try:
                cur = conn.execute(f"SELECT COUNT(*) FROM {TABLE_FERIADOS}")
                if cur.fetchone()[0] > 0:
                    return []
            finally:
                conn.close()
        if builder == "feriados":
            spec = get_partition_spec("feriados")
            if silver_exists("feriados", spec.partition_key, SNAPSHOT_VALUE, "parquet"):
                return ["snapshot"]
            return []
        return []
    table, date_col = meta
    return missing_persisted_dates(table, date_col, ready, db_path)


def sync_status_report(
    end: str | None = None,
    *,
    start: str | None = None,
    check_persist: bool = True,
    db_path: Any = None,
) -> dict[str, dict[str, list[str]]]:
    """Summary of gaps per layer for mandatory datasets/builders."""
    range_start = sync_start_date(start)
    range_end = sync_end_date(end)
    bronze: dict[str, list[str]] = {}
    silver: dict[str, list[str]] = {}
    gold: dict[str, list[str]] = {}
    for ds in MANDATORY_DATASETS:
        bg = bronze_gaps(ds, range_start, range_end)
        if bg:
            bronze[ds] = bg
        sg = silver_gaps(ds, range_start, range_end)
        if sg:
            silver[ds] = sg
    for builder in MANDATORY_BUILDERS:
        gg = gold_gaps(
            builder, range_start, range_end, db_path=db_path, check_persist=check_persist
        )
        if gg:
            gold[builder] = gg
    return {"bronze": bronze, "silver": silver, "gold": gold}


def has_mandatory_gaps(report: dict[str, dict[str, list[str]]]) -> bool:
    return bool(report["bronze"] or report["silver"] or report["gold"])


__all__ = [
    "MANDATORY_BUILDERS",
    "MANDATORY_DATASETS",
    "bronze_gaps",
    "gold_gaps",
    "has_mandatory_gaps",
    "silver_gaps",
    "sync_status_report",
]
