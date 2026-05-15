CREATE INDEX IF NOT EXISTS ix_msdata
ON MERCADO_SECUNDARIO (data_referencia);

CREATE INDEX IF NOT EXISTS ix_ms_titulo
ON MERCADO_SECUNDARIO (tipo_titulo, data_vencimento);

CREATE INDEX IF NOT EXISTS ix_tp_tipo_venc
ON TITULOS_PUBLICOS (tipo_titulo, data_vencimento);