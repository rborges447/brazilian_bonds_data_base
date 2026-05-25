-- BMF contracts and daily adjustments.

CREATE TABLE IF NOT EXISTS CONTRATOS_BMF (
    ticker TEXT NOT NULL PRIMARY KEY,
    codigo_isin TEXT,
    data_vencimento TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS AJUSTES_BMF (
    ticker TEXT NOT NULL,
    data_referencia TEXT NOT NULL,
    taxa_ajuste REAL,
    quantidade_ajuste REAL,
    PRIMARY KEY (ticker, data_referencia),
    FOREIGN KEY (ticker) REFERENCES CONTRATOS_BMF (ticker)
);
