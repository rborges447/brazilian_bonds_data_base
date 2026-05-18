"""Bronze: UpToData BMF adjustments (raw parquet per day)."""

from __future__ import annotations

from contracts import ExtractResult
from pipelines.bronze._split import pick_date_column
from pipelines.bronze.incremental import missing_partition_values
from pipelines.bronze.partitioning import get_partition_spec
from pipelines.bronze.writer import write_dataframe_partitions
from providers.uptodata import scrap_ajustes_bmf_for_dates


def extract_ajustes_bmf(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("ajustes_bmf")
    to_fetch = missing_partition_values(spec.dataset, dates)
    if not to_fetch:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    df = scrap_ajustes_bmf_for_dates(to_fetch)
    if df.empty:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    date_col = pick_date_column(df, spec.date_col_candidates)
    if date_col is None:
        from pipelines.bronze.writer import write_partition_parquet

        day = to_fetch[0]
        path = write_partition_parquet(
            spec.dataset, spec.partition_key, day, df, spec.artifact_ext
        )
        return ExtractResult(path=path, row_count=len(df), segment_keys=[day])

    keys, rows, last_path = write_dataframe_partitions(
        df, spec, date_col, only_values=set(to_fetch)
    )
    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)
