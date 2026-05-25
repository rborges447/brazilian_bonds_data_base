-- Market settlements. Columns aligned with liquidacoes_mercado materializer.

CREATE TABLE IF NOT EXISTS LIQUIDACOES_MERCADO (
    tipo_titulo TEXT NOT NULL,
    data_vencimento TEXT NOT NULL,
    data_referencia TEXT NOT NULL,
    qtd_operacoes INTEGER,
    qtd_titulos REAL,
    pu_medio REAL,
    expressao TEXT,
    data_base TEXT,
    codigo_selic TEXT,
    codigo_isin TEXT,
    status TEXT NOT NULL DEFAULT 'ATIVO'
        CHECK (status IN ('ATIVO', 'INATIVO', 'SUSPENSO', 'CANCELADO', 'RESGATADO')),
    PRIMARY KEY (tipo_titulo, data_vencimento, data_referencia),
    FOREIGN KEY (tipo_titulo, data_vencimento)
        REFERENCES TITULOS_PUBLICOS (tipo_titulo, data_vencimento)
);
