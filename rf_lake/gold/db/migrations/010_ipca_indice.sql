-- IPCA mensal (SIDRA): número-índice e variação mensal (%)
-- ref_month armazenado como ISO YYYY-MM-DD (sempre dia 01).

CREATE TABLE IF NOT EXISTS IPCA_INDICE (
    ref_month  TEXT NOT NULL,  -- ISO YYYY-MM-DD (primeiro dia do mês)
    ipca_index REAL,
    ipca_mom   REAL,
    PRIMARY KEY (ref_month)
) WITHOUT ROWID;

