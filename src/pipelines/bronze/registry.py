"""Bronze extractor registry."""

from __future__ import annotations

from contracts import BronzeExtractor, ExtractResult
from pipelines.bronze.extractors.ajustes_bmf import extract_ajustes_bmf
from pipelines.bronze.extractors.cdi import extract_cdi
from pipelines.bronze.extractors.feriados import extract_feriados
from pipelines.bronze.extractors.ipca_indice import extract_ipca_indice
from pipelines.bronze.extractors.leiloes import extract_leiloes
from pipelines.bronze.extractors.liquidacoes_mercado import extract_liquidacoes_mercado
from pipelines.bronze.extractors.mercado_secundario import extract_mercado_secundario
from pipelines.bronze.extractors.projecoes import extract_projecoes
from pipelines.bronze.extractors.ptax import extract_ptax

EXTRACTORS: dict[str, BronzeExtractor] = {
    "mercado_secundario": extract_mercado_secundario,
    "liquidacoes_mercado": extract_liquidacoes_mercado,
    "ajustes_bmf": extract_ajustes_bmf,
    "leiloes": extract_leiloes,
    "ipca_indice": extract_ipca_indice,
    "feriados": extract_feriados,
    "projecoes": extract_projecoes,
    "cdi": extract_cdi,
    "ptax": extract_ptax,
}


def extract_dataset(name: str, dates: list[str]) -> ExtractResult:
    fn = EXTRACTORS.get(name)
    if fn is None:
        raise ValueError(f"Dataset has no bronze extractor: {name}")
    return fn(dates)
