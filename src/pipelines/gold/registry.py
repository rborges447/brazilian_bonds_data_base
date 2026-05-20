"""Dispatch silver frames to materializers (pass-through) or builders (transform)."""

from __future__ import annotations

from typing import Any, Callable

from pipelines.gold.contracts import (
    BUILDER_NAMES,
    BUILDER_SILVER_DATASETS,
    BuilderContext,
    BuilderName,
    PASS_THROUGH_NAMES,
    SilverFrames,
)
from pipelines.gold.materializers.cdi import from_silver as cdi_from_silver
from pipelines.gold.materializers.feriados import from_silver as feriados_from_silver
from pipelines.gold.materializers.bmf import from_silver as bmf_from_silver
from pipelines.gold.materializers.liquidacoes_mercado import (
    from_silver as liquidacoes_mercado_from_silver,
)
from pipelines.gold.materializers.mercado_secundario import (
    from_silver as mercado_secundario_from_silver,
)
from pipelines.gold.materializers.ptax import from_silver as ptax_from_silver

MaterializerFn = Callable[[SilverFrames, BuilderContext], Any]

MATERIALIZERS: dict[BuilderName, MaterializerFn] = {
    "feriados": feriados_from_silver,
    "cdi": cdi_from_silver,
    "ptax": ptax_from_silver,
    "bmf": bmf_from_silver,
    "mercado_secundario": mercado_secundario_from_silver,
    "liquidacoes_mercado": liquidacoes_mercado_from_silver,
}

_NOT_IMPLEMENTED_MSG = (
    "Gold builder '{name}' is not implemented. "
    "Silver datasets loaded: {datasets}. "
    "Add build() in pipelines.gold.builders.{name}."
)


def build(name: BuilderName, silver: SilverFrames, ctx: BuilderContext) -> Any:
    """
    Produce gold-ready value for ``name`` from silver frames.

    Pass-through names use ``materializers/``; others use ``builders/`` (phase B).
    """
    if name not in BUILDER_NAMES:
        raise ValueError(f"Unknown gold builder: {name}. Allowed: {BUILDER_NAMES}")

    if name in MATERIALIZERS:
        return MATERIALIZERS[name](silver, ctx)

    loaded = ", ".join(silver.keys()) or "(empty)"
    raise NotImplementedError(
        _NOT_IMPLEMENTED_MSG.format(
            name=name,
            datasets=loaded or ", ".join(BUILDER_SILVER_DATASETS.get(name, ())),
        )
    )
