"""Bronze: ANBIMA projections (JSON per reference_month, split by mes_referencia)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.contracts import ExtractResult
from app.core.dates import months_in_range
from app.lake.bronze._split import months_from_candidate_dates
from app.lake.bronze.extractors._projecoes_split import (
    flatten_projecoes_payload,
    group_records_by_reference_month,
    partition_key_to_mes_ano,
    partitions_to_refresh_projecoes,
    write_merged_partition,
)
from app.core.partitioning import get_partition_spec
from app.lake.bronze.paths import bronze_partition_path
from app.providers.anbima import AnbimaClient


def _candidate_months(dates: list[str]) -> list[str]:
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
    """
    Fetch ANBIMA projections and write hive partitions by mes_referencia.

    Always refreshes active calendar months (prev/current/next). Merges new
    coletas into existing JSON per partition (dedupe by data_coleta).
    """
    spec = get_partition_spec("projecoes")
    candidates = _candidate_months(dates)
    to_refresh = partitions_to_refresh_projecoes(candidates)
    if not to_refresh:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    client = AnbimaClient()
    query_months = {partition_key_to_mes_ano(key) for key in to_refresh}

    touched_partitions: set[str] = set()
    total_rows = 0
    last_path: Path | None = None

    latest = client.fetch_projecoes_latest()
    if latest is not None:
        for ref_month, records in group_records_by_reference_month(
            flatten_projecoes_payload(latest)
        ).items():
            if records:
                write_merged_partition(ref_month, records)
                touched_partitions.add(ref_month)
                total_rows += len(records)

    for mes, ano in sorted(query_months):
        payload = client.fetch_projecoes(mes, ano)
        if payload is None:
            continue
        grouped = group_records_by_reference_month(flatten_projecoes_payload(payload))
        for ref_month, records in grouped.items():
            if not records:
                continue
            write_merged_partition(ref_month, records)
            touched_partitions.add(ref_month)
            total_rows += len(records)
            last_path = bronze_partition_path(
                spec.dataset, spec.partition_key, ref_month, spec.artifact_ext
            )

    keys = sorted(touched_partitions)
    if keys and last_path is None:
        last_path = bronze_partition_path(
            spec.dataset, spec.partition_key, keys[-1], spec.artifact_ext
        )

    return ExtractResult(
        path=last_path,
        row_count=total_rows,
        segment_keys=keys,
    )
