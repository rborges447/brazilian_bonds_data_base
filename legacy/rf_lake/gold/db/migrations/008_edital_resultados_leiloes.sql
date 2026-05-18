-- Tabela única de leilões (resultados + oferta).
-- PK/FK seguem a lógica do edital (chave composta).
CREATE TABLE IF NOT EXISTS LEILOES (
    numero_edital                    INTEGER NOT NULL,
    tipo_titulo                      TEXT    NOT NULL,  -- FK para TITULOS_PUBLICOS(tipo_titulo, data_vencimento)
    data_vencimento                  TEXT    NOT NULL,  -- ISO YYYY-MM-DD
    data_referencia                  TEXT    NOT NULL,  -- ISO YYYY-MM-DD

    -- Coluna do "edital" (agora vem do endpoint de resultados)
    oferta                           INTEGER,

    -- Colunas de resultados
    quantidade_aceita                INTEGER,
    percentual_corte                 REAL,
    oferta_segunda_volta             INTEGER,
    financeiro_aceito                REAL,
    financeiro_aceito_segunda_volta  REAL,
    quantidade_aceita_segunda_volta  INTEGER,
    pu_medio                         REAL,
    taxa_media                       REAL,

    PRIMARY KEY (tipo_titulo, data_vencimento, data_referencia, numero_edital),
    FOREIGN KEY (tipo_titulo, data_vencimento)
        REFERENCES TITULOS_PUBLICOS(tipo_titulo, data_vencimento)
) WITHOUT ROWID;
 