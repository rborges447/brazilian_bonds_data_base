-- VNA diário (ANBIMA): 1 linha por data_referencia + codigo_selic.

CREATE TABLE IF NOT EXISTS VNA (
    data_referencia TEXT NOT NULL,
    codigo_selic INTEGER NOT NULL,
    tipo_correcao TEXT NOT NULL,
    "index" REAL NOT NULL,
    data_validade TEXT NOT NULL,
    vna REAL NOT NULL,
    vna_ajustado REAL,
    PRIMARY KEY (data_referencia, codigo_selic)
);

CREATE INDEX IF NOT EXISTS idx_vna_data ON VNA (data_referencia);
