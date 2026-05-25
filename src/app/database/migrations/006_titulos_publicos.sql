-- Public bonds master (dimension for mercado, liquidações, leilões).

CREATE TABLE IF NOT EXISTS TITULOS_PUBLICOS (
    tipo_titulo TEXT NOT NULL,
    data_vencimento TEXT NOT NULL,
    expressao TEXT,
    data_base TEXT,
    codigo_selic TEXT,
    codigo_isin TEXT,
    status TEXT NOT NULL DEFAULT 'ATIVO'
        CHECK (status IN ('ATIVO', 'INATIVO', 'SUSPENSO', 'CANCELADO', 'RESGATADO')),
    PRIMARY KEY (tipo_titulo, data_vencimento)
);
