"""Gold layer: silver → builders → gold-ready objects (pipeline-driven)."""

from app.lake.gold.contracts import (
    BUILDER_NAMES,
    BUILDER_SILVER_DATASETS,
    BuilderContext,
    BuilderName,
    BmfGoldValue,
    CdiGoldValue,
    FeriadosGoldValue,
    IpcaDictGoldValue,
    LeiloesGoldValue,
    LiquidacoesMercadoGoldValue,
    MercadoSecundarioGoldValue,
    PtaxGoldValue,
    GoldMaterialized,
    PASS_THROUGH_NAMES,
    SilverFrames,
    is_snapshot_only_builder,
)
from app.lake.gold.orchestrator import GoldOrchestrator
from app.lake.gold import registry

__all__ = [
    "BUILDER_NAMES",
    "BUILDER_SILVER_DATASETS",
    "BuilderContext",
    "BuilderName",
    "BmfGoldValue",
    "CdiGoldValue",
    "FeriadosGoldValue",
    "IpcaDictGoldValue",
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
