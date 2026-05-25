"""Bronze: BCB PTAX USD closing rates (raw parquet per day)."""

from __future__ import annotations

from app.contracts import ExtractResult
from app.lake.bronze._split import pick_date_column
from app.lake.bronze.incremental import missing_partition_values
from app.core.partitioning import get_partition_spec
from app.lake.bronze.writer import write_dataframe_partitions
from app.providers import fetch_ptax_usd


def extract_ptax(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("ptax")
    to_fetch = missing_partition_values(spec.dataset, dates)
    if not to_fetch:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    df = fetch_ptax_usd(start_date=min(to_fetch), end_date=max(to_fetch))
    if df.empty:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    date_col = pick_date_column(df, spec.date_col_candidates) or "data"
    keys, rows, last_path = write_dataframe_partitions(
        df, spec, date_col, only_values=set(to_fetch)
    )
    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)
