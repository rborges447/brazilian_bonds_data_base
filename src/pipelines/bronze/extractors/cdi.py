"""Bronze: BCB SGS CDI daily rate (raw parquet per day)."""

from __future__ import annotations

from contracts import ExtractResult
from pipelines.bronze._split import pick_date_column
from pipelines.bronze.incremental import missing_partition_values
from pipelines.bronze.partitioning import get_partition_spec
from pipelines.bronze.writer import write_dataframe_partitions
from providers import fetch_cdi_daily


def extract_cdi(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("cdi")
    to_fetch = missing_partition_values(spec.dataset, dates)
    if not to_fetch:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    df = fetch_cdi_daily(start_date=min(to_fetch), end_date=max(to_fetch))
    if df.empty:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    date_col = pick_date_column(df, spec.date_col_candidates) or "data"
    keys, rows, last_path = write_dataframe_partitions(
        df, spec, date_col, only_values=set(to_fetch)
    )
    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)
