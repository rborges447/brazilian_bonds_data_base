# =========================
# TITULOS_PUBLICOS
# =========================

TITULOS_PUBLICOS_COLUMNS = [
    "expressao",
    "data_vencimento",
    "tipo_titulo",
    "data_base",
    "codigo_selic",
    "codigo_isin",
    "status",
]

TITULOS_PUBLICOS_REQUIRED = [
    "tipo_titulo",
    "data_vencimento",
]

# Note: schema PK is (tipo_titulo, data_vencimento)

# =========================
# MERCADO_SECUNDARIO
# =========================

MERCADO_SECUNDARIO_COLUMNS = [
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
    "taxa_anbima",
    "intervalo_min_d0",
    "intervalo_max_d0",
    "intervalo_min_d1",
    "intervalo_max_d1",
    "pu",
]

MERCADO_SECUNDARIO_REQUIRED = [
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
]

MERCADO_SECUNDARIO_NUMERIC = [
    "taxa_anbima",
    "intervalo_min_d0",
    "intervalo_max_d0",
    "intervalo_min_d1",
    "intervalo_max_d1",
    "pu",
]

# =========================
# LIQUIDACOES_MERCADO
# =========================

LIQUIDACOES_MERCADO_COLUMNS = [
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
    "qtd_operacoes",
    "qtd_titulos",
    "pu_medio",
]

LIQUIDACOES_MERCADO_REQUIRED = [
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
]

LIQUIDACOES_MERCADO_NUMERIC = [
    "qtd_operacoes",
    "qtd_titulos",
    "pu_medio",
]

# =========================
# CONTRATOS_BMF
# =========================

CONTRATOS_BMF_COLUMNS = [
    "ticker",
    "codigo_isin",
    "data_vencimento",
]

CONTRATOS_BMF_REQUIRED = [
    "ticker",
    "data_vencimento",
]

# =========================
# AJUSTES_BMF
# =========================

AJUSTES_BMF_COLUMNS = [
    "ticker",
    "data_referencia",
    "taxa_ajuste",
    "quantidade_ajuste",
]

AJUSTES_BMF_REQUIRED = [
    "ticker",
    "data_referencia",
]

AJUSTES_BMF_NUMERIC = [
    "taxa_ajuste",
    "quantidade_ajuste",
]

# =========================
# RENAMES (API -> database)
# =========================

MERCADO_SECUNDARIO_RENAME_MAP = {
    "taxa_indicativa": "taxa_anbima",
}

LIQUIDACOES_MERCADO_RENAME_MAP = {
    "DATA MOV": "data_referencia",
    "NUM DE OPER": "qtd_operacoes",
    "QUANT NEGOCIADA": "qtd_titulos",
    "PU MED": "pu_medio",
    "SIGLA": "tipo_titulo",
    "VENCIMENTO": "data_vencimento",
}

AJUSTES_BMF_RENAME_MAP = {
    "RptDt": "data_referencia",
    "TckrSymb": "ticker",
    "ISIN": "codigo_isin",
    "XprtnDt": "data_vencimento",
    "AdjstdQtTax": "taxa_ajuste",
    "AdjstdQt": "quantidade_ajuste",
}

# =========================
# LEILOES
# =========================

LEILOES_COLUMNS = [
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

LEILOES_REQUIRED = [
    "numero_edital",
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
]

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

# =========================
# PROJECOES
# =========================

PROJECOES_COLUMNS = [
    "indice",
    "tipo_projecao",
    "data_coleta",
    "ref_month",
    "variacao_projetada",
    "data_validade",
]

PROJECOES_REQUIRED = [
    "indice",
    "tipo_projecao",
    "data_coleta",
    "ref_month",
]

PROJECOES_NUMERIC = [
    "variacao_projetada",
]

PROJECOES_RENAME_MAP = {
    "mes_referencia": "ref_month",
}

# =========================
# RENAMES (API -> database) - continued
# =========================

# Auctions (Treasury auction API results)
LEILOES_RENAME_MAP = {
    "data_leilao": "data_referencia",
    "titulo": "tipo_titulo",
    "vencimento": "data_vencimento",
}

# =========================
# FERIADOS
# =========================

FERIADOS_COLUMNS = ["data"]
FERIADOS_REQUIRED = ["data"]
