CREATE TABLE IF NOT EXISTS CONTRATOS_BMF (
    ticker          TEXT    NOT NULL PRIMARY KEY,
    codigo_isin     TEXT,
    data_vencimento  TEXT    NOT NULL  -- formato ISO: YYYY-MM-DD
);

CREATE TABLE IF NOT EXISTS AJUSTES_BMF (
    ticker              TEXT    NOT NULL,              -- FK para CONTRATOS_BMF(ticker)
    data_referencia     TEXT    NOT NULL,              -- ISO YYYY-MM-DD
    taxa_ajuste         REAL,
    quantidade_ajuste   REAL,
    PRIMARY KEY (ticker, data_referencia),
    FOREIGN KEY (ticker) REFERENCES CONTRATOS_BMF(ticker)
) WITHOUT ROWID;
