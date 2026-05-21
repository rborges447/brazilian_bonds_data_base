"""Gold layer: silver → builders → gold-ready objects (pipeline-driven)."""

from pipelines.gold.contracts import (
    BUILDER_NAMES,
    BUILDER_SILVER_DATASETS,
    BuilderContext,
    BuilderName,
    BmfGoldValue,
    CdiGoldValue,
    FeriadosGoldValue,
    LeiloesGoldValue,
    LiquidacoesMercadoGoldValue,
    MercadoSecundarioGoldValue,
    PtaxGoldValue,
    GoldMaterialized,
    PASS_THROUGH_NAMES,
    SilverFrames,
    is_snapshot_only_builder,
)
from pipelines.gold.orchestrator import GoldOrchestrator
from pipelines.gold import registry

__all__ = [
    "BUILDER_NAMES",
    "BUILDER_SILVER_DATASETS",
    "BuilderContext",
    "BuilderName",
    "BmfGoldValue",
    "CdiGoldValue",
    "FeriadosGoldValue",
    "LeiloesGoldValue",
    "LiquidacoesMercadoGoldValue",
    "MercadoSecundarioGoldValue",
    "PtaxGoldValue",
    "GoldMaterialized",
    "GoldOrchestrator",
    "PASS_THROUGH_NAMES",
    "SilverFrames",
    "is_snapshot_only_builder",
    "registry",
]
