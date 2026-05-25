"""Bronze: SIDRA IPCA table (raw sidrapy parquet per reference month)."""



from __future__ import annotations



from app.contracts import ExtractResult

from app.core.sync_range import sync_ipca_months

from app.lake.bronze._split import (

    months_from_candidate_dates,

    pick_date_column,

    split_dataframe_by_partition,

)

from app.lake.bronze.incremental import missing_partition_values

from app.core.partitioning import get_partition_spec

from app.lake.bronze.writer import write_partition_parquet

from app.providers.sidra import SidraIpcaClient





def _allowed_months(dates: list[str]) -> set[str]:

    if dates:

        return set(months_from_candidate_dates(dates))

    return set(sync_ipca_months())





def extract_ipca_indice(dates: list[str]) -> ExtractResult:

    spec = get_partition_spec("ipca_indice")

    df = SidraIpcaClient().fetch_table_ipca()

    if df.empty:

        return ExtractResult(path=None, row_count=0, segment_keys=[])



    date_col = pick_date_column(df, spec.date_col_candidates)

    if date_col is None:

        return ExtractResult(path=None, row_count=0, segment_keys=[])



    parts = split_dataframe_by_partition(df, date_col, spec.granularity)

    allowed = _allowed_months(dates)

    candidate_months = sorted(m for m in parts if m in allowed)

    to_write = missing_partition_values(spec.dataset, candidate_months)



    keys: list[str] = []

    rows = 0

    last_path = None

    for month in to_write:

        chunk = parts.get(month)

        if chunk is None or chunk.empty:

            continue

        last_path = write_partition_parquet(

            spec.dataset, spec.partition_key, month, chunk, spec.artifact_ext

        )

        keys.append(month)

        rows += len(chunk)



    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)


