CREATE INDEX IF NOT EXISTS ix_lm_data
ON LIQUIDACOES_MERCADO (data_referencia);

CREATE INDEX IF NOT EXISTS ix_lm_titulo
ON LIQUIDACOES_MERCADO (tipo_titulo, data_vencimento);
