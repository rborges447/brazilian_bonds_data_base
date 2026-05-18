"""Shared JSON partition extract loop (internal)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from contracts import ExtractResult
from pipelines.bronze.incremental import missing_partition_values
from pipelines.bronze.partitioning import DatasetPartitionSpec
from pipelines.bronze.writer import write_partition_json


def extract_json_partitions(
    spec: DatasetPartitionSpec,
    candidate_values: list[str],
    fetch: Callable[[str], Any | None],
) -> ExtractResult:
    """Fetch and write one JSON artifact per missing partition value."""
    to_fetch = missing_partition_values(spec.dataset, candidate_values)
    if not to_fetch:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    keys: list[str] = []
    rows = 0
    last_path: Path | None = None

    for value in to_fetch:
        payload = fetch(value)
        if payload is None:
            continue
        last_path = write_partition_json(
            spec.dataset,
            spec.partition_key,
            value,
            payload,
            spec.artifact_ext,
        )
        keys.append(value)
        if isinstance(payload, list):
            rows += len(payload)
        else:
            rows += 1

    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)
