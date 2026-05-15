-- Projeções IPCA/IGP-M (ANBIMA): indice, tipo_projecao, data_coleta, ref_month (MM/YYYY), variacao_projetada, data_validade.

CREATE TABLE IF NOT EXISTS PROJECOES (
    indice             TEXT NOT NULL,
    tipo_projecao      TEXT NOT NULL,
    data_coleta        TEXT NOT NULL,   -- ISO YYYY-MM-DD
    ref_month          TEXT NOT NULL,  -- MM/YYYY (como na fonte)
    variacao_projetada REAL,
    data_validade      TEXT,           -- ISO YYYY-MM-DD (nullable)
    PRIMARY KEY (indice, tipo_projecao, ref_month, data_coleta)
) WITHOUT ROWID;
