"""
Gold layer contracts: builder names, silver inputs, pipeline context.

Gold-ready values for SQL:
- single-column snapshots → list (e.g. feriados)
- tabular datasets → pd.DataFrame with named columns (e.g. cdi, ptax, bmf, mercado_secundario)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

BuilderName = Literal[
    "feriados",
    "cdi",
    "ptax",
    "bmf",
    "mercado_secundario",
    "liquidacoes_mercado",
    "leiloes",
    "ipca_dict",
    "vna_lft",
]

BUILDER_NAMES: tuple[BuilderName, ...] = (
    "feriados",
    "cdi",
    "ptax",
    "bmf",
    "mercado_secundario",
    "liquidacoes_mercado",
    "leiloes",
    "ipca_dict",
    "vna_lft",
)

SilverFrames = dict[str, pd.DataFrame]

# Names served by materializers/ (no transform in builders/).
PASS_THROUGH_NAMES: tuple[BuilderName, ...] = (
    "feriados",
    "cdi",
    "ptax",
    "bmf",
    "mercado_secundario",
    "liquidacoes_mercado",
    "leiloes",
)

FeriadosGoldValue = list[str]
CdiGoldValue = pd.DataFrame
PtaxGoldValue = pd.DataFrame
BmfGoldValue = pd.DataFrame
MercadoSecundarioGoldValue = pd.DataFrame
LiquidacoesMercadoGoldValue = pd.DataFrame
LeiloesGoldValue = pd.DataFrame
IpcaDictGoldValue = pd.DataFrame

BUILDER_SILVER_DATASETS: dict[BuilderName, tuple[str, ...]] = {
    "feriados": ("feriados",),
    "cdi": ("cdi",),
    "ptax": ("ptax",),
    "bmf": ("ajustes_bmf",),
    "mercado_secundario": ("mercado_secundario",),
    "liquidacoes_mercado": ("liquidacoes_mercado",),
    "leiloes": ("leiloes",),
    "ipca_dict": ("ipca_indice", "projecoes"),
    "vna_lft": (),
}


def is_snapshot_only_builder(name: BuilderName) -> bool:
    """True when all silver inputs are snapshot partitions (full read, no date range)."""
    from app.core.partitioning import is_snapshot_dataset

    datasets = BUILDER_SILVER_DATASETS.get(name, ())
    return bool(datasets) and all(is_snapshot_dataset(ds) for ds in datasets)


@dataclass
class BuilderContext:
    """Per-run options for a gold builder (filled by the gold pipeline)."""

    start_date: str | None = None
    end_date: str | None = None
    dates: list[str] | None = None
    as_of_date: pd.Timestamp | None = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class GoldMaterialized:
    """Result of one orchestrator run: silver inputs + gold-ready value."""

    name: BuilderName
    silver: SilverFrames
    value: Any
