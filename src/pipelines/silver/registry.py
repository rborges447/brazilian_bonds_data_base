"""Silver transform registry (dataset → normalize_partition)."""

from __future__ import annotations

from contracts import SilverTransform
from pipelines.silver.transforms import (
    ajustes_bmf,
    cdi,
    feriados,
    ipca_indice,
    leiloes,
    liquidacoes_mercado,
    mercado_secundario,
    projecoes,
    ptax,
)

TRANSFORMS: dict[str, SilverTransform] = {
    "mercado_secundario": mercado_secundario.normalize_partition,
    "liquidacoes_mercado": liquidacoes_mercado.normalize_partition,
    "ajustes_bmf": ajustes_bmf.normalize_partition,
    "leiloes": leiloes.normalize_partition,
    "feriados": feriados.normalize_partition,
    "ipca_indice": ipca_indice.normalize_partition,
    "projecoes": projecoes.normalize_partition,
    "cdi": cdi.normalize_partition,
    "ptax": ptax.normalize_partition,
}


def get_transform(name: str) -> SilverTransform:
    fn = TRANSFORMS.get(name)
    if fn is None:
        raise ValueError(f"Dataset has no silver transform: {name}")
    return fn
