"""Dataset registry metadata (date modes per pipeline)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.partitioning import PARTITION_SPECS, PIPELINE_NAMES

DateMode = Literal["missing_dates", "run_always"]
# run_always: extract always runs; monthly (ipca, projecoes) or snapshot (feriados).


@dataclass
class DatasetConfig:
    name: str
    date_mode: DateMode


DATASETS: dict[str, DatasetConfig] = {
    "mercado_secundario": DatasetConfig("mercado_secundario", "missing_dates"),
    "liquidacoes_mercado": DatasetConfig("liquidacoes_mercado", "missing_dates"),
    "ajustes_bmf": DatasetConfig("ajustes_bmf", "missing_dates"),
    "leiloes": DatasetConfig("leiloes", "missing_dates"),
    "ipca_indice": DatasetConfig("ipca_indice", "run_always"),
    "projecoes": DatasetConfig("projecoes", "run_always"),
    "feriados": DatasetConfig("feriados", "run_always"),
    "cdi": DatasetConfig("cdi", "missing_dates"),
    "ptax": DatasetConfig("ptax", "missing_dates"),
}


def get_dataset_config(name: str) -> DatasetConfig:
    cfg = DATASETS.get(name)
    if cfg is None:
        raise ValueError(f"Unknown dataset: {name}. Allowed: {list(PIPELINE_NAMES)}")
    return cfg


assert set(DATASETS) == set(PARTITION_SPECS), (
    f"DATASETS keys must match PARTITION_SPECS: "
    f"only_in_datasets={set(DATASETS) - set(PARTITION_SPECS)}, "
    f"only_in_specs={set(PARTITION_SPECS) - set(DATASETS)}"
)
