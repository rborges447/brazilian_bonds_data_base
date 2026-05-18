CREATE TABLE IF NOT EXISTS TITULOS_PUBLICOS (
        expressao TEXT,
        data_vencimento TEXT NOT NULL,  -- formato ISO: YYYY-MM-DD
        tipo_titulo TEXT NOT NULL,
        data_base TEXT,
        codigo_selic TEXT,
        codigo_isin TEXT,
        status TEXT NOT NULL DEFAULT 'ATIVO'
               CHECK (status IN ('ATIVO','INATIVO','SUSPENSO','CANCELADO','RESGATADO')),
        PRIMARY KEY (tipo_titulo, data_vencimento)
    ) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS MERCADO_SECUNDARIO (
        tipo_titulo      TEXT    NOT NULL,              -- FK para TITULOS_PUBLICOS(tipo_titulo, data_vencimento)
        data_vencimento  TEXT    NOT NULL,              -- ISO YYYY-MM-DD
        data_referencia  TEXT    NOT NULL,              -- ISO YYYY-MM-DD
        taxa_anbima      REAL,
        intervalo_min_d0 REAL,
        intervalo_max_d0 REAL,
        intervalo_min_d1 REAL,
        intervalo_max_d1 REAL,
        pu               REAL,
        PRIMARY KEY (tipo_titulo, data_vencimento, data_referencia),
        FOREIGN KEY (tipo_titulo, data_vencimento) REFERENCES TITULOS_PUBLICOS(tipo_titulo, data_vencimento)
    ) WITHOUT ROWID;