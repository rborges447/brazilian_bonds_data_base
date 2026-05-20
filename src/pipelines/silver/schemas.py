"""Canonical silver column layouts and rename maps (port of legacy contracts + schema)."""

from __future__ import annotations

MERCADO_SECUNDARIO_RENAME_MAP = {
    "taxa_indicativa": "taxa_anbima",
}

MERCADO_SECUNDARIO_NUMERIC = [
    "taxa_anbima",
    "intervalo_min_d0",
    "intervalo_max_d0",
    "intervalo_min_d1",
    "intervalo_max_d1",
    "pu",
]

LIQUIDACOES_MERCADO_RENAME_MAP = {
    "DATA MOV": "data_referencia",
    "NUM DE OPER": "qtd_operacoes",
    "QUANT NEGOCIADA": "qtd_titulos",
    "PU MED": "pu_medio",
    "SIGLA": "tipo_titulo",
    "VENCIMENTO": "data_vencimento",
}

LIQUIDACOES_MERCADO_NUMERIC = [
    "qtd_operacoes",
    "qtd_titulos",
    "pu_medio",
]

AJUSTES_BMF_RENAME_MAP = {
    "RptDt": "data_referencia",
    "TckrSymb": "ticker",
    "ISIN": "codigo_isin",
    "XprtnDt": "data_vencimento",
    "AdjstdQtTax": "taxa_ajuste",
    "AdjstdQt": "quantidade_ajuste",
}

AJUSTES_BMF_NUMERIC = [
    "taxa_ajuste",
    "quantidade_ajuste",
]

LEILOES_RENAME_MAP = {
    "data_leilao": "data_referencia",
    "titulo": "tipo_titulo",
    "vencimento": "data_vencimento",
}

LEILOES_NUMERIC = [
    "numero_edital",
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

PROJECOES_RENAME_MAP = {
    "mes_referencia": "ref_month",
}

PROJECOES_NUMERIC = [
    "variacao_projetada",
]

CDI_RENAME_MAP = {
    "estimativa_taxa_selic": "cdi",
}

CDI_NUMERIC = ["cdi"]

PTAX_RENAME_MAP = {
    "data": "data_referencia",
    "taxa_compra": "ptax_compra",
    "taxa_venda": "ptax_venda",
}

PTAX_NUMERIC = ["ptax_compra", "ptax_venda"]
