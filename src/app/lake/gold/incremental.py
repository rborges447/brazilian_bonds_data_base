"""Gold incremental: candidates and gaps vs silver / SQLite."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import get_settings
import pandas as pd

from app.core.dates import _month_start_from_iso, months_in_range
from app.core.partitioning import SNAPSHOT_VALUE, get_partition_spec, is_snapshot_dataset
from app.core.sync_range import (
    sync_business_days,
    sync_calendar_days,
    sync_end_date,
    sync_ipca_month_start,
    sync_months,
    sync_start_date,
)
from app.database.connection import get_connection
from app.database.schema import (
    TABLE_AJUSTES_BMF,
    TABLE_CDI,
    TABLE_FERIADOS,
    TABLE_IPCA_DICT,
    TABLE_LEILOES,
    TABLE_LIQUIDACOES_MERCADO,
    TABLE_MERCADO_SECUNDARIO,
    TABLE_PTAX,
    TABLE_VNA,
)
from app.lake.gold.contracts import BUILDER_NAMES, BUILDER_SILVER_DATASETS, BuilderName
from app.lake.silver.storage import partition_artifact_exists

def _month_first_from_day(day: str) -> str:
    return _month_start_from_iso(day).isoformat()


BUILDER_TABLE: dict[BuilderName, tuple[str, str]] = {
    "cdi": (TABLE_CDI, "data_referencia"),
    "ptax": (TABLE_PTAX, "data_referencia"),
    "bmf": (TABLE_AJUSTES_BMF, "data_referencia"),
    "mercado_secundario": (TABLE_MERCADO_SECUNDARIO, "data_referencia"),
    "liquidacoes_mercado": (TABLE_LIQUIDACOES_MERCADO, "data_referencia"),
    "leiloes": (TABLE_LEILOES, "data_referencia"),
    "ipca_dict": (TABLE_IPCA_DICT, "data_referencia"),
    "feriados": (TABLE_FERIADOS, "data"),
    "vna": (TABLE_VNA, "data_referencia"),
}


def candidates_for_builder(
    builder: BuilderName,
    end: str | None = None,
    *,
    start: str | None = None,
) -> list[str]:
    """Partition values in the canonical sync window for this builder."""
    if builder == "feriados":
        return []
    if builder == "ipca_dict":
        return sync_calendar_days(end=end, start=start)
    datasets = BUILDER_SILVER_DATASETS.get(builder, ())
    if not datasets:
        return []
    spec = get_partition_spec(datasets[0])
    if spec.granularity == "month":
        return sync_months(end=end, start=start)
    return sync_business_days(end=end, start=start)


def _silver_ext(dataset: str) -> str:
    return "parquet"


def _values_with_silver(dataset: str, candidates: list[str]) -> list[str]:
    if not candidates:
        return []
    spec = get_partition_spec(dataset)
    ext = _silver_ext(dataset)
    ready: list[str] = []
    for value in candidates:
        if partition_artifact_exists(dataset, spec.partition_key, value, ext):
            ready.append(value)
    return ready


def _ipca_silver_months_required_for_day(
    day: str,
    *,
    ipca_ready: set[str] | None = None,
) -> list[str]:
    """
    Monthly IPCA partitions required to build ``day``.

    When the calendar month's index is not in silver yet (e.g. May before SIDRA
    release), only lookback through the previous month is required — matching
    ``build_for_date`` / ``read_silver_range(..., only_existing=True)``.
    """
    as_of_month = _month_first_from_day(day)
    if ipca_ready is not None and as_of_month not in ipca_ready:
        prev = (
            pd.Timestamp(as_of_month) - pd.DateOffset(months=1)
        ).strftime("%Y-%m-01")
        return months_in_range(sync_ipca_month_start(), prev)
    return months_in_range(sync_ipca_month_start(), as_of_month)


def _dates_ipca_dict_buildable(candidates: list[str]) -> list[str]:
    """
    Calendar days with projecoes silver for the calendar month and full IPCA lookback.

    Avoids false gold gaps when only the as_of month partition exists but fechado M-1
    months (pre-DATA_START_DATE) are still missing from silver.
    """
    calendar_months = {_month_first_from_day(d) for d in candidates}
    if candidates:
        max_month = max(_month_first_from_day(d) for d in candidates)
        ipca_probe = months_in_range(sync_ipca_month_start(), max_month)
    else:
        ipca_probe = []
    ipca_ready = set(_values_with_silver("ipca_indice", ipca_probe))
    proj_ready = set(_values_with_silver("projecoes", sorted(calendar_months)))
    buildable: list[str] = []
    for d in candidates:
        m = _month_first_from_day(d)
        if m not in proj_ready:
            continue
        required = _ipca_silver_months_required_for_day(d, ipca_ready=ipca_ready)
        if all(r in ipca_ready for r in required):
            buildable.append(d)
    return buildable


def _dates_silver_ready(builder: BuilderName, candidates: list[str]) -> list[str]:
    if builder == "feriados":
        spec = get_partition_spec("feriados")
        if partition_artifact_exists(
            "feriados", spec.partition_key, SNAPSHOT_VALUE, "parquet"
        ):
            return []
        return []

    if builder == "ipca_dict":
        return _dates_ipca_dict_buildable(candidates)

    datasets = BUILDER_SILVER_DATASETS.get(builder, ())
    if not datasets:
        return []

    primary = datasets[0]
    spec = get_partition_spec(primary)
    if spec.granularity == "month":
        month_cands = sorted({_month_first_from_day(d) for d in candidates})
        ready_months = set(_values_with_silver(primary, month_cands))
        return [d for d in candidates if _month_first_from_day(d) in ready_months]

    ready_days = set(_values_with_silver(primary, candidates))
    if len(datasets) == 1:
        return [d for d in candidates if d in ready_days]

    out: list[str] = []
    for day in candidates:
        if day not in ready_days:
            continue
        if all(
            day in set(_values_with_silver(ds, [day]))
            for ds in datasets[1:]
            if not is_snapshot_dataset(ds)
        ):
            out.append(day)
    return out


def _existing_dates_in_table(
    table: str,
    date_col: str,
    candidates: list[str],
    db_path: Path | str | None,
) -> set[str]:
    if not candidates:
        return set()
    path = db_path or get_settings().db_path
    if not Path(path).is_file():
        return set()
    start = min(candidates)
    end = max(candidates)
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            f"SELECT DISTINCT {date_col} FROM {table} "
            f"WHERE {date_col} >= ? AND {date_col} <= ?",
            (start, end),
        )
        return {str(row[0])[:10] for row in cur.fetchall()}
    finally:
        conn.close()


def missing_persisted_dates(
    table: str,
    date_col: str,
    candidates: list[str],
    db_path: Any = None,
) -> list[str]:
    """Candidates with silver coverage expected but no row in SQLite."""
    existing = _existing_dates_in_table(table, date_col, candidates, db_path)
    return [d for d in candidates if d not in existing]


def missing_materialize_dates(
    builder: BuilderName,
    candidates: list[str],
    *,
    persist: bool = False,
    db_path: Any = None,
) -> list[str]:
    """Dates to materialize: silver ready and not yet persisted when ``persist``."""
    ready = _dates_silver_ready(builder, candidates)
    if not persist:
        return ready
    meta = BUILDER_TABLE.get(builder)
    if meta is None:
        return ready
    table, date_col = meta
    if builder == "feriados":
        path = db_path or get_settings().db_path
        if not Path(path).is_file():
            return ready
        conn = get_connection(db_path)
        try:
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
            if cur.fetchone()[0] == 0:
                return ready
        finally:
            conn.close()
        return []
    missing = missing_persisted_dates(table, date_col, ready, db_path)
    return missing


__all__ = [
    "BUILDER_TABLE",
    "_dates_ipca_dict_buildable",
    "candidates_for_builder",
    "missing_materialize_dates",
    "missing_persisted_dates",
]
