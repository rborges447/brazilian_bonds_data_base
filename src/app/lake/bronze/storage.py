"""Bronze artifact presence checks (shared by writer, reader, incremental)."""

from __future__ import annotations

from app.lake.bronze.paths import bronze_partition_path


def partition_artifact_exists(dataset: str, partition_key: str, value: str, ext: str) -> bool:
    path = bronze_partition_path(dataset, partition_key, value, ext)
    return path.is_file() and path.stat().st_size > 0
