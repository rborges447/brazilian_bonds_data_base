"""Bronze: ANBIMA projections (raw JSON per reference month)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from contracts import ExtractResult
from models.dates import months_in_range
from pipelines.bronze._split import months_from_candidate_dates
from pipelines.bronze.incremental import missing_partition_values
from pipelines.bronze.partitioning import get_partition_spec
from pipelines.bronze.writer import write_partition_json
from providers.anbima import AnbimaClient


def _months_to_fetch(dates: list[str]) -> list[str]:
    if dates:
        return months_from_candidate_dates(dates)
    today = date.today()
    prev_m = today.month - 1 if today.month > 1 else 12
    prev_y = today.year if today.month > 1 else today.year - 1
    return months_in_range(
        f"{prev_y:04d}-{prev_m:02d}-01",
        f"{today.year:04d}-{today.month:02d}-01",
    )


def extract_projecoes(dates: list[str], backfill: bool = False) -> ExtractResult:
    del backfill  # range comes from task dates (DATA_START_DATE .. target)
    spec = get_partition_spec("projecoes")
    candidates = _months_to_fetch(dates)
    to_fetch = missing_partition_values(spec.dataset, candidates)
    if not to_fetch:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    client = AnbimaClient()
    keys: list[str] = []
    rows = 0
    last_path: Path | None = None

    for month_key in to_fetch:
        year = int(month_key[:4])
        month = int(month_key[5:7])
        payload = client.fetch_projecoes(month, year)
        if payload is None:
            continue
        last_path = write_partition_json(
            spec.dataset,
            spec.partition_key,
            month_key,
            payload,
            spec.artifact_ext,
        )
        keys.append(month_key)
        if isinstance(payload, list):
            rows += len(payload)
        else:
            rows += 1

    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)
