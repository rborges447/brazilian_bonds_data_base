-- Treasury auctions. Columns aligned with leiloes materializer.

CREATE TABLE IF NOT EXISTS LEILOES (
    numero_edital INTEGER NOT NULL,
    tipo_titulo TEXT NOT NULL,
    data_vencimento TEXT NOT NULL,
    data_referencia TEXT NOT NULL,
    oferta INTEGER,
    quantidade_aceita INTEGER,
    percentual_corte REAL,
    oferta_segunda_volta INTEGER,
    financeiro_aceito REAL,
    financeiro_aceito_segunda_volta REAL,
    quantidade_aceita_segunda_volta INTEGER,
    pu_medio REAL,
    taxa_media REAL,
    PRIMARY KEY (tipo_titulo, data_vencimento, data_referencia, numero_edital),
    FOREIGN KEY (tipo_titulo, data_vencimento)
        REFERENCES TITULOS_PUBLICOS (tipo_titulo, data_vencimento)
);
