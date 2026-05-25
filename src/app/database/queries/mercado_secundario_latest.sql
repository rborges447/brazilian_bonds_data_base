WITH latest_dates AS (
    SELECT data_referencia
    FROM MERCADO_SECUNDARIO
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT tipo_titulo, data_vencimento, data_referencia, taxa_anbima, intervalo_min_d0, intervalo_max_d0, intervalo_min_d1, intervalo_max_d1, pu, expressao, data_base, codigo_selic, codigo_isin, taxa_compra, taxa_venda, desvio_padrao, status
FROM MERCADO_SECUNDARIO
WHERE data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY data_referencia DESC, tipo_titulo, data_vencimento
