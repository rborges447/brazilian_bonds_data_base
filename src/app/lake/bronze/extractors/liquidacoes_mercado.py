"""Bronze: BCB NegE settlements (raw parquet per day)."""

from __future__ import annotations

from app.contracts import ExtractResult
from app.lake.bronze._split import pick_date_column
from app.lake.bronze.incremental import missing_partition_values
from app.core.partitioning import get_partition_spec
from app.lake.bronze.writer import write_dataframe_partitions
from app.providers.bcb import fetch_negociacoes_bruto_por_datas


def extract_liquidacoes_mercado(dates: list[str]) -> ExtractResult:
    spec = get_partition_spec("liquidacoes_mercado")
    to_fetch = missing_partition_values(spec.dataset, dates)
    if not to_fetch:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    df = fetch_negociacoes_bruto_por_datas(to_fetch, date_column="DATA MOV")
    if df.empty:
        return ExtractResult(path=None, row_count=0, segment_keys=[])

    date_col = pick_date_column(df, spec.date_col_candidates) or "DATA MOV"
    keys, rows, last_path = write_dataframe_partitions(
        df, spec, date_col, only_values=set(to_fetch)
    )
    return ExtractResult(path=last_path, row_count=rows, segment_keys=keys)
