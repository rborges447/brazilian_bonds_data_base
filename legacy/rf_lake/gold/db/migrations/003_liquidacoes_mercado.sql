CREATE TABLE IF NOT EXISTS LIQUIDACOES_MERCADO (
    tipo_titulo      TEXT    NOT NULL,              -- FK para TITULOS_PUBLICOS(tipo_titulo, data_vencimento)
    data_vencimento  TEXT    NOT NULL,              -- ISO YYYY-MM-DD
    data_referencia  TEXT    NOT NULL,              -- ISO YYYY-MM-DD
    qtd_operacoes    INTEGER,
    qtd_titulos      REAL,
    pu_medio         REAL,
    PRIMARY KEY (tipo_titulo, data_vencimento, data_referencia),
    FOREIGN KEY (tipo_titulo, data_vencimento) REFERENCES TITULOS_PUBLICOS(tipo_titulo, data_vencimento)
) WITHOUT ROWID;
