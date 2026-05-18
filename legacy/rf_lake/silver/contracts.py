"""
Canonical schemas per dataset/table.

Defines expected DataFrame layouts after normalization.
"""

from __future__ import annotations

from typing import List

# ============================================================================
# MERCADO_SECUNDARIO
# ============================================================================

MERCADO_SECUNDARIO_CANONICAL_COLUMNS = [
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
    "expressao",
    "data_base",
    "codigo_selic",
    "codigo_isin",
    "status",
    "taxa_anbima",
    "intervalo_min_d0",
    "intervalo_max_d0",
    "intervalo_min_d1",
    "intervalo_max_d1",
    "pu",
]

MERCADO_SECUNDARIO_REQUIRED_COLUMNS = [
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
]

# ============================================================================
# LIQUIDACOES_MERCADO
# ============================================================================

LIQUIDACOES_MERCADO_CANONICAL_COLUMNS = [
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
    "expressao",
    "data_base",
    "codigo_selic",
    "codigo_isin",
    "status",
    "qtd_operacoes",
    "qtd_titulos",
    "pu_medio",
]

LIQUIDACOES_MERCADO_REQUIRED_COLUMNS = [
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
]

# ============================================================================
# AJUSTES_BMF
# ============================================================================

AJUSTES_BMF_CANONICAL_COLUMNS = [
    "ticker",
    "data_referencia",
    "codigo_isin",
    "data_vencimento",
    "taxa_ajuste",
    "quantidade_ajuste",
]

AJUSTES_BMF_REQUIRED_COLUMNS = [
    "ticker",
    "data_referencia",
]

# ============================================================================
# LEILOES
# ============================================================================

LEILOES_CANONICAL_COLUMNS = [
    "numero_edital",
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
    "oferta",
    "quantidade_aceita",
    "percentual_corte",
    "oferta_segunda_volta",
    "financeiro_aceito",
    "financeiro_aceito_segunda_volta",
    "quantidade_aceita_segunda_volta",
    "pu_medio",
    "taxa_media",
]

LEILOES_REQUIRED_COLUMNS = [
    "numero_edital",
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
]
