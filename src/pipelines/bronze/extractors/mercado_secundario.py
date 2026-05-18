"""Bronze: ANBIMA mercado secundário TPF (raw JSON per day)."""

from __future__ import annotations

from pathlib import Path

from contracts import ExtractResult
from pipelines.bronze.incremental import missing_partition_values
from pipelines.bronze.partitioning import get_partition_spec
from pipelines.bronze.writer import write_partition_json
from providers.anbima import AnbimaClient, MERCADO_SECUNDARIO_TPF


def extract_mercado_secundario(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("mercado_secundario")
    to_fetch = missing_partition_values(spec.dataset, dates)
    if not to_fetch:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    client = AnbimaClient()
    keys: list[str] = []
    rows = 0
    last_path: Path | None = None

    for day in to_fetch:
        payload = client.fetch_by_date(MERCADO_SECUNDARIO_TPF, day)
        if payload is None:
            continue
        last_path = write_partition_json(
            spec.dataset, spec.partition_key, day, payload, spec.artifact_ext
        )
        keys.append(day)
        if isinstance(payload, list):
            rows += len(payload)
        else:
            rows += 1

    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)
