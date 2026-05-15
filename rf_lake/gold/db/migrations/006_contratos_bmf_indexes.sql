CREATE INDEX IF NOT EXISTS ix_cb_ticker
ON CONTRATOS_BMF (ticker);

CREATE INDEX IF NOT EXISTS ix_ab_data
ON AJUSTES_BMF (data_referencia);
