"""Bronze: ANBIMA SELIC estimate (raw parquet per day)."""

from __future__ import annotations

import pandas as pd

from contracts import ExtractResult
from pipelines.bronze._split import pick_date_column
from pipelines.bronze.incremental import missing_partition_values
from pipelines.bronze.partitioning import get_partition_spec
from pipelines.bronze.writer import write_dataframe_partitions
from providers.anbima import fetch_estimativa_selic


def extract_cdi(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("cdi")
    to_fetch = missing_partition_values(spec.dataset, dates)
    if not to_fetch:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    frames: list[pd.DataFrame] = []
    for day in sorted(to_fetch):
        df_day = fetch_estimativa_selic(day)
        if not df_day.empty:
            frames.append(df_day)
    if not frames:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    df = pd.concat(frames, ignore_index=True)
    date_col = pick_date_column(df, spec.date_col_candidates) or "data_referencia"
    keys, rows, last_path = write_dataframe_partitions(
        df, spec, date_col, only_values=set(to_fetch)
    )
    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)
