"""Bronze: Tesouro auction results (raw JSON list per auction day)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.contracts import ExtractResult
from app.lake.bronze._split import auction_date_from_record, to_iso_date_string
from app.lake.bronze.incremental import missing_partition_values
from app.core.partitioning import get_partition_spec
from app.lake.bronze.writer import write_partition_json
from app.providers.tesouro import get_resultados_by_dates


def extract_leiloes(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("leiloes")
    to_fetch = set(missing_partition_values(spec.dataset, dates))
    if not to_fetch:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    records = get_resultados_by_dates(dates)
    by_day: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        if not isinstance(record, dict):
            continue
        day = auction_date_from_record(record)
        if day is None:
            continue
        day = to_iso_date_string(day) or day
        if day in to_fetch or day in dates:
            by_day[day].append(record)

    keys: list[str] = []
    rows = 0
    last_path: Path | None = None
    for day in sorted(by_day):
        if day not in to_fetch and day not in set(dates):
            continue
        payload = by_day[day]
        last_path = write_partition_json(
            spec.dataset, spec.partition_key, day, payload, spec.artifact_ext
        )
        keys.append(day)
        rows += len(payload)

    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)
