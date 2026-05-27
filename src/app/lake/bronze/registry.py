"""Bronze extractor registry."""

from __future__ import annotations

from app.contracts import BronzeExtractor, ExtractResult
from app.lake.bronze.extractors.ajustes_bmf import extract_ajustes_bmf
from app.lake.bronze.extractors.cdi import extract_cdi
from app.lake.bronze.extractors.feriados import extract_feriados
from app.lake.bronze.extractors.ipca_indice import extract_ipca_indice
from app.lake.bronze.extractors.leiloes import extract_leiloes
from app.lake.bronze.extractors.liquidacoes_mercado import extract_liquidacoes_mercado
from app.lake.bronze.extractors.mercado_secundario import extract_mercado_secundario
from app.lake.bronze.extractors.projecoes import extract_projecoes
from app.lake.bronze.extractors.ptax import extract_ptax
from app.lake.bronze.extractors.vna import extract_vna

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
    "vna": extract_vna,
}


def extract_dataset(name: str, dates: list[str]) -> ExtractResult:
    fn = EXTRACTORS.get(name)
    if fn is None:
        raise ValueError(f"Dataset has no bronze extractor: {name}")
    return fn(dates)
