CREATE INDEX IF NOT EXISTS idx_leiloes_data_ref
ON LEILOES (data_referencia);

CREATE INDEX IF NOT EXISTS idx_leiloes_titulo_id
ON LEILOES (tipo_titulo, data_vencimento);

CREATE INDEX IF NOT EXISTS idx_leiloes_numero_edital
ON LEILOES (numero_edital);
