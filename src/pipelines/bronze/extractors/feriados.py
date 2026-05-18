"""Bronze: national holidays snapshot (raw XLS as parquet)."""

from __future__ import annotations

import pandas as pd

from contracts import ExtractResult
from pipelines.bronze.incremental import missing_partition_values
from pipelines.bronze.partitioning import SNAPSHOT_VALUE, get_partition_spec
from pipelines.bronze.writer import write_partition_parquet
from providers.feriados import fetch_feriados


def extract_feriados(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("feriados")
    missing = missing_partition_values(spec.dataset, [SNAPSHOT_VALUE])
    if not missing:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    raw = fetch_feriados()
    if not raw:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    df = pd.DataFrame({"Data": raw})
    path = write_partition_parquet(
        spec.dataset,
        spec.partition_key,
        SNAPSHOT_VALUE,
        df,
        spec.artifact_ext,
    )
    return ExtractResult(
        path=path,
        row_count=len(df),
        segment_keys=[SNAPSHOT_VALUE],
    )
