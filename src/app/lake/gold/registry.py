"""Dispatch silver frames to materializers (pass-through) or builders (transform)."""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

from app.lake.gold.contracts import (
    BUILDER_NAMES,
    BUILDER_SILVER_DATASETS,
    BuilderContext,
    BuilderName,
    PASS_THROUGH_NAMES,
    SilverFrames,
)
from app.lake.gold.materializers.cdi import from_silver as cdi_from_silver
from app.lake.gold.materializers.feriados import from_silver as feriados_from_silver
from app.lake.gold.materializers.bmf import from_silver as bmf_from_silver
from app.lake.gold.materializers.leiloes import from_silver as leiloes_from_silver
from app.lake.gold.materializers.liquidacoes_mercado import (
    from_silver as liquidacoes_mercado_from_silver,
)
from app.lake.gold.materializers.mercado_secundario import (
    from_silver as mercado_secundario_from_silver,
)
from app.lake.gold.materializers.ptax import from_silver as ptax_from_silver
from app.lake.gold.builders.ipca_dict import build_for_date
from app.lake.gold.materializers.ipca_dict import to_dataframe as ipca_dict_to_dataframe

MaterializerFn = Callable[[SilverFrames, BuilderContext], Any]

MATERIALIZERS: dict[BuilderName, MaterializerFn] = {
    "feriados": feriados_from_silver,
    "cdi": cdi_from_silver,
    "ptax": ptax_from_silver,
    "bmf": bmf_from_silver,
    "mercado_secundario": mercado_secundario_from_silver,
    "liquidacoes_mercado": liquidacoes_mercado_from_silver,
    "leiloes": leiloes_from_silver,
}

def _build_ipca_dict(silver: SilverFrames, ctx: BuilderContext) -> Any:
    if "feriados" not in ctx.extras:
        raise ValueError(
            "ipca_dict requires ctx.extras['feriados'] (set by orchestrator)."
        )
    feriados = ctx.extras["feriados"]
    if not ctx.dates:
        return ipca_dict_to_dataframe([])

    if "ipca_indice" not in silver or "projecoes" not in silver:
        raise KeyError(
            "Silver datasets 'ipca_indice' and 'projecoes' required for ipca_dict."
        )
    ipca_full = silver["ipca_indice"]
    proj_full = silver["projecoes"]
    if ipca_full is None or ipca_full.empty:
        raise ValueError("Silver ipca_indice is empty. Run silver pipeline first.")
    if proj_full is None or proj_full.empty:
        raise ValueError("Silver projecoes is empty. Run silver pipeline first.")

    pairs: list[tuple[str, dict]] = []
    for raw_date in ctx.dates:
        date = raw_date.strip()[:10]
        try:
            built = build_for_date(
                date,
                ipca_monthly=ipca_full,
                projecoes=proj_full,
                feriados=feriados,
            )
        except (ValueError, KeyError) as exc:
            logger.warning("ipca_dict skip %s: %s", date, exc)
            continue
        pairs.append((date, built))
    return ipca_dict_to_dataframe(pairs)


_NOT_IMPLEMENTED_MSG = (
    "Gold builder '{name}' is not implemented. "
    "Silver datasets loaded: {datasets}. "
    "Add build() in lake.gold.builders.{name}."
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

    if name == "ipca_dict":
        return _build_ipca_dict(silver, ctx)

    loaded = ", ".join(silver.keys()) or "(empty)"
    raise NotImplementedError(
        _NOT_IMPLEMENTED_MSG.format(
            name=name,
            datasets=loaded or ", ".join(BUILDER_SILVER_DATASETS.get(name, ())),
        )
    )
