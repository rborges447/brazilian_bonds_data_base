"""Gold table names and column metadata (schema v2)."""

from __future__ import annotations

import pandas as pd

from app.lake.gold.materializers.ipca_dict import IPCA_DICT_COLUMNS

TABLE_FERIADOS = "FERIADOS"
TABLE_CDI = "CDI"
TABLE_PTAX = "PTAX"
TABLE_VNA = "VNA"
TABLE_IPCA_DICT = "IPCA_DICT"
TABLE_TITULOS_PUBLICOS = "TITULOS_PUBLICOS"
TABLE_MERCADO_SECUNDARIO = "MERCADO_SECUNDARIO"
TABLE_LIQUIDACOES_MERCADO = "LIQUIDACOES_MERCADO"
TABLE_LEILOES = "LEILOES"
TABLE_CONTRATOS_BMF = "CONTRATOS_BMF"
TABLE_AJUSTES_BMF = "AJUSTES_BMF"
TABLE_JOB_RUNS = "job_runs"

FERIADOS_COLUMNS: tuple[str, ...] = ("data",)
CDI_COLUMNS: tuple[str, ...] = ("data_referencia", "cdi")
PTAX_COLUMNS: tuple[str, ...] = ("data_referencia", "ptax_compra", "ptax_venda")
VNA_COLUMNS: tuple[str, ...] = (
    "data_referencia",
    "codigo_selic",
    "tipo_correcao",
    "index",
    "data_validade",
    "vna",
    "vna_ajustado",
)

TITULOS_PUBLICOS_COLUMNS: tuple[str, ...] = (
    "tipo_titulo",
    "data_vencimento",
    "expressao",
    "data_base",
    "codigo_selic",
    "codigo_isin",
    "status",
)

MERCADO_SECUNDARIO_COLUMNS: tuple[str, ...] = (
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
    "taxa_anbima",
    "intervalo_min_d0",
    "intervalo_max_d0",
    "intervalo_min_d1",
    "intervalo_max_d1",
    "pu",
    "expressao",
    "data_base",
    "codigo_selic",
    "codigo_isin",
    "taxa_compra",
    "taxa_venda",
    "desvio_padrao",
    "status",
)

LIQUIDACOES_MERCADO_COLUMNS: tuple[str, ...] = (
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
    "qtd_operacoes",
    "qtd_titulos",
    "pu_medio",
    "expressao",
    "data_base",
    "codigo_selic",
    "codigo_isin",
    "status",
)

LEILOES_COLUMNS: tuple[str, ...] = (
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
)

CONTRATOS_BMF_COLUMNS: tuple[str, ...] = ("ticker", "codigo_isin", "data_vencimento")
AJUSTES_BMF_COLUMNS: tuple[str, ...] = (
    "ticker",
    "data_referencia",
    "taxa_ajuste",
    "quantidade_ajuste",
)

BUSINESS_TABLES_V2: tuple[str, ...] = (
    TABLE_FERIADOS,
    TABLE_CDI,
    TABLE_PTAX,
    TABLE_VNA,
    TABLE_IPCA_DICT,
    TABLE_TITULOS_PUBLICOS,
    TABLE_MERCADO_SECUNDARIO,
    TABLE_LIQUIDACOES_MERCADO,
    TABLE_LEILOES,
    TABLE_CONTRATOS_BMF,
    TABLE_AJUSTES_BMF,
)


def validate_dataframe_columns(
    table_name: str,
    df: pd.DataFrame,
    expected: tuple[str, ...],
) -> None:
    """Raise if DataFrame is missing required columns or has unexpected extras."""
    if df is None or df.empty:
        return
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"{table_name}: missing columns {missing}")
    extra = [c for c in df.columns if c not in expected]
    if extra:
        raise ValueError(f"{table_name}: unexpected columns {extra}")


__all__ = [
    "AJUSTES_BMF_COLUMNS",
    "BUSINESS_TABLES_V2",
    "CDI_COLUMNS",
    "CONTRATOS_BMF_COLUMNS",
    "FERIADOS_COLUMNS",
    "IPCA_DICT_COLUMNS",
    "LEILOES_COLUMNS",
    "LIQUIDACOES_MERCADO_COLUMNS",
    "MERCADO_SECUNDARIO_COLUMNS",
    "PTAX_COLUMNS",
    "TABLE_AJUSTES_BMF",
    "TABLE_CDI",
    "TABLE_CONTRATOS_BMF",
    "TABLE_FERIADOS",
    "TABLE_IPCA_DICT",
    "TABLE_JOB_RUNS",
    "TABLE_LEILOES",
    "TABLE_LIQUIDACOES_MERCADO",
    "TABLE_MERCADO_SECUNDARIO",
    "TABLE_PTAX",
    "TABLE_TITULOS_PUBLICOS",
    "TABLE_VNA",
    "TITULOS_PUBLICOS_COLUMNS",
    "VNA_COLUMNS",
    "validate_dataframe_columns",
]
