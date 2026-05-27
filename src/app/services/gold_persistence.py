"""Persist gold materialized outputs to SQLite (repositories only — no business logic)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.lake.gold.contracts import BuilderName, GoldMaterialized
from app.repositories.bmf import BmfRepository
from app.repositories.cdi import CdiRepository
from app.repositories.feriados import FeriadosRepository
from app.repositories.ipca_dict import IpcaDictRepository
from app.repositories.leiloes import LeiloesRepository
from app.repositories.liquidacoes_mercado import LiquidacoesMercadoRepository
from app.repositories.mercado_secundario import MercadoSecundarioRepository
from app.repositories.ptax import PtaxRepository
from app.repositories.vna import VnaRepository


def persist_materialized(
    result: GoldMaterialized,
    *,
    db_path: Any = None,
) -> int:
    """Write one builder result to SQL; returns rows written."""
    name: BuilderName = result.name
    value = result.value

    if name == "feriados":
        if not isinstance(value, list):
            raise TypeError("feriados gold value must be list[str]")
        return FeriadosRepository().upsert(value, db_path=db_path)

    if not isinstance(value, pd.DataFrame):
        raise TypeError(f"{name} gold value must be DataFrame for persistence")

    repos: dict[BuilderName, Any] = {
        "cdi": CdiRepository(),
        "ptax": PtaxRepository(),
        "ipca_dict": IpcaDictRepository(),
        "bmf": BmfRepository(),
        "mercado_secundario": MercadoSecundarioRepository(),
        "liquidacoes_mercado": LiquidacoesMercadoRepository(),
        "leiloes": LeiloesRepository(),
        "vna": VnaRepository(),
    }
    repo = repos.get(name)
    if repo is None:
        raise ValueError(f"No repository for builder: {name}")
    return repo.upsert(value, db_path=db_path)
