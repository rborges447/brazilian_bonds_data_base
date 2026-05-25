-- Secondary market TPF quotes. Columns aligned with mercado_secundario materializer.

CREATE TABLE IF NOT EXISTS MERCADO_SECUNDARIO (
    tipo_titulo TEXT NOT NULL,
    data_vencimento TEXT NOT NULL,
    data_referencia TEXT NOT NULL,
    taxa_anbima REAL,
    intervalo_min_d0 REAL,
    intervalo_max_d0 REAL,
    intervalo_min_d1 REAL,
    intervalo_max_d1 REAL,
    pu REAL,
    expressao TEXT,
    data_base TEXT,
    codigo_selic TEXT,
    codigo_isin TEXT,
    taxa_compra REAL,
    taxa_venda REAL,
    desvio_padrao REAL,
    status TEXT NOT NULL DEFAULT 'ATIVO'
        CHECK (status IN ('ATIVO', 'INATIVO', 'SUSPENSO', 'CANCELADO', 'RESGATADO')),
    PRIMARY KEY (tipo_titulo, data_vencimento, data_referencia),
    FOREIGN KEY (tipo_titulo, data_vencimento)
        REFERENCES TITULOS_PUBLICOS (tipo_titulo, data_vencimento)
);
