CREATE INDEX IF NOT EXISTS idx_mercado_data ON MERCADO_SECUNDARIO (data_referencia);
CREATE INDEX IF NOT EXISTS idx_mercado_titulo ON MERCADO_SECUNDARIO (tipo_titulo, data_vencimento);
CREATE INDEX IF NOT EXISTS idx_liquidacoes_data ON LIQUIDACOES_MERCADO (data_referencia);
CREATE INDEX IF NOT EXISTS idx_leiloes_data ON LEILOES (data_referencia);
CREATE INDEX IF NOT EXISTS idx_ajustes_bmf_data ON AJUSTES_BMF (data_referencia);
CREATE INDEX IF NOT EXISTS idx_ipca_dict_ref_month ON IPCA_DICT (ref_month_atual);
CREATE INDEX IF NOT EXISTS idx_titulos_tipo_venc ON TITULOS_PUBLICOS (tipo_titulo, data_vencimento);
