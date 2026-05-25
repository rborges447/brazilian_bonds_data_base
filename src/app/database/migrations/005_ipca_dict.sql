-- IPCA dict daily. Aligned with lake.gold.materializers.ipca_dict.IPCA_DICT_COLUMNS.
-- Silver keeps monthly ipca_indice/projecoes; gold exposes one row per business day.

CREATE TABLE IF NOT EXISTS IPCA_DICT (
    data_referencia TEXT NOT NULL PRIMARY KEY,
    ultimo_mes_ipca TEXT,
    ref_month_atual TEXT,
    ref_month_anterior TEXT,
    indice_ipca_data_base REAL,
    indice_ipca_fechado_atual REAL,
    indice_ipca_fechado_anterior REAL,
    var_ipca_atual REAL,
    var_ipca_ant REAL,
    ipca_proj REAL,
    ipca_usado REAL,
    usa_fechado INTEGER NOT NULL DEFAULT 0 CHECK (usa_fechado IN (0, 1)),
    data_coleta_referencia TEXT,
    ipca_proj_data_coleta TEXT,
    inicio_mes_ipca TEXT,
    fim_mes_ipca TEXT
);
