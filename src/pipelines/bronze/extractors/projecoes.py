"""Bronze: ANBIMA projections (raw JSON per reference month)."""

from __future__ import annotations

from datetime import date

from contracts import ExtractResult
from models.dates import months_in_range
from pipelines.bronze._extract_json import extract_json_partitions
from pipelines.bronze._split import months_from_candidate_dates
from pipelines.bronze.partitioning import get_partition_spec
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


def extract_projecoes(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("projecoes")
    candidates = _months_to_fetch(dates)
    client = AnbimaClient()

    def _fetch(month_key: str):
        year = int(month_key[:4])
        month = int(month_key[5:7])
        return client.fetch_projecoes(month, year)

    return extract_json_partitions(spec, candidates, _fetch)
