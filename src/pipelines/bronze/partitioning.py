"""Partition specs per bronze dataset (hive keys and artifact format)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Granularity = Literal["day", "month", "snapshot"]


@dataclass(frozen=True)
class DatasetPartitionSpec:
    dataset: str
    partition_key: str
    granularity: Granularity
    artifact_ext: str
    date_col_candidates: tuple[str, ...] = ()


PARTITION_SPECS: dict[str, DatasetPartitionSpec] = {
    "mercado_secundario": DatasetPartitionSpec(
        dataset="mercado_secundario",
        partition_key="data",
        granularity="day",
        artifact_ext="json",
        date_col_candidates=(),
    ),
    "liquidacoes_mercado": DatasetPartitionSpec(
        dataset="liquidacoes_mercado",
        partition_key="data",
        granularity="day",
        artifact_ext="parquet",
        date_col_candidates=("DATA MOV", "data", "DATA", "Data Negociação", "data_negociacao"),
    ),
    "ajustes_bmf": DatasetPartitionSpec(
        dataset="ajustes_bmf",
        partition_key="data",
        granularity="day",
        artifact_ext="parquet",
        date_col_candidates=("RptDt", "data_referencia"),
    ),
    "leiloes": DatasetPartitionSpec(
        dataset="leiloes",
        partition_key="data",
        granularity="day",
        artifact_ext="json",
        date_col_candidates=("dataLeilao", "data_leilao", "data_referencia"),
    ),
    "ipca_indice": DatasetPartitionSpec(
        dataset="ipca_indice",
        partition_key="reference_month",
        granularity="month",
        artifact_ext="parquet",
        # sidrapy raw columns (D2C = YYYYMM); canonical names exist only after silver mapping
        date_col_candidates=("D2C", "DATA_CODIGO", "DATA", "ref_month"),
    ),
    "feriados": DatasetPartitionSpec(
        dataset="feriados",
        partition_key="snapshot",
        granularity="snapshot",
        artifact_ext="parquet",
        date_col_candidates=(),
    ),
    "projecoes": DatasetPartitionSpec(
        dataset="projecoes",
        partition_key="reference_month",
        granularity="month",
        artifact_ext="json",
        date_col_candidates=(),
    ),
    "cdi": DatasetPartitionSpec(
        dataset="cdi",
        partition_key="data",
        granularity="day",
        artifact_ext="parquet",
        date_col_candidates=("data",),
    ),
}

PIPELINE_NAMES: tuple[str, ...] = tuple(PARTITION_SPECS.keys())

SNAPSHOT_VALUE = "1"


def get_partition_spec(dataset: str) -> DatasetPartitionSpec:
    spec = PARTITION_SPECS.get(dataset)
    if spec is None:
        raise ValueError(f"Unknown bronze dataset: {dataset}")
    return spec


def is_snapshot_dataset(dataset: str) -> bool:
    return get_partition_spec(dataset).granularity == "snapshot"
