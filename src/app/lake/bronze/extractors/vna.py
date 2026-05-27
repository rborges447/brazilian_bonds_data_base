"""Bronze: ANBIMA VNA (raw JSON per day)."""

from __future__ import annotations

from app.contracts import ExtractResult
from app.core.partitioning import get_partition_spec
from app.lake.bronze._extract_json import extract_json_partitions
from app.providers.anbima import AnbimaClient


def extract_vna(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("vna")
    client = AnbimaClient()
    return extract_json_partitions(
        spec,
        dates,
        lambda day: client.fetch_vna(day),
    )
