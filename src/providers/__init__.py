"""
External data providers: HTTP clients and file readers grouped by source.

- anbima: OAuth API (mercado secundário, projeções)
- feriados: public ANBIMA holiday XLS
- bcb: BCB NegE ZIP settlements
- tesouro: Tesouro Nacional auction results
- sidra: IBGE IPCA via sidrapy
- uptodata: local BMF adjustment CSVs
"""

from providers.anbima import AnbimaAuth, AnbimaClient, MERCADO_SECUNDARIO_TPF, PROJECOES, VNA
from providers.bcb import build_negociacoes_url, fetch_negociacoes_bruto_por_datas
from providers.feriados import fetch_feriados
from providers.sidra import SidraIpcaClient
from providers.tesouro import get_resultados, get_resultados_by_dates
from providers.uptodata import scrap_ajustes_bmf, scrap_ajustes_bmf_for_dates

__all__ = [
    "AnbimaAuth",
    "AnbimaClient",
    "MERCADO_SECUNDARIO_TPF",
    "PROJECOES",
    "VNA",
    "build_negociacoes_url",
    "fetch_feriados",
    "fetch_negociacoes_bruto_por_datas",
    "get_resultados",
    "get_resultados_by_dates",
    "SidraIpcaClient",
    "scrap_ajustes_bmf",
    "scrap_ajustes_bmf_for_dates",
]
