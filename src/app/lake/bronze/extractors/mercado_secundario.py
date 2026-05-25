"""Bronze: ANBIMA mercado secundário TPF (raw JSON per day)."""

from __future__ import annotations

from app.contracts import ExtractResult
from app.lake.bronze._extract_json import extract_json_partitions
from app.core.partitioning import get_partition_spec
from app.providers.anbima import AnbimaClient, MERCADO_SECUNDARIO_TPF


def extract_mercado_secundario(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("mercado_secundario")
    client = AnbimaClient()
    return extract_json_partitions(
        spec,
        dates,
        lambda day: client.fetch_by_date(MERCADO_SECUNDARIO_TPF, day),
    )
