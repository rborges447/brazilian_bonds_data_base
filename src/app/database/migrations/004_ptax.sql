-- PTAX USD daily (BCB). Aligned with lake.gold.materializers.ptax.

CREATE TABLE IF NOT EXISTS PTAX (
    data_referencia TEXT NOT NULL PRIMARY KEY,
    ptax_compra REAL,
    ptax_venda REAL
);
