SELECT * FROM (
SELECT
    m.tipo_titulo,
    m.data_vencimento,
    m.data_referencia,
    m.taxa_anbima,
    m.intervalo_min_d0,
    m.intervalo_max_d0,
    m.intervalo_min_d1,
    m.intervalo_max_d1,
    m.pu,
    m.expressao AS expressao_mercado,
    m.data_base AS data_base_mercado,
    m.codigo_selic AS codigo_selic_mercado,
    m.codigo_isin AS codigo_isin_mercado,
    m.taxa_compra,
    m.taxa_venda,
    m.desvio_padrao,
    m.status AS status_mercado,
    l.qtd_operacoes,
    l.qtd_titulos,
    l.pu_medio AS pu_medio_liq,
    l.expressao AS expressao_liq,
    l.data_base AS data_base_liq,
    l.codigo_selic AS codigo_selic_liq,
    l.codigo_isin AS codigo_isin_liq,
    l.status AS status_liq
FROM MERCADO_SECUNDARIO m
LEFT JOIN LIQUIDACOES_MERCADO l
    ON m.tipo_titulo = l.tipo_titulo
   AND m.data_vencimento = l.data_vencimento
   AND m.data_referencia = l.data_referencia


UNION ALL

SELECT
    l.tipo_titulo,
    l.data_vencimento,
    l.data_referencia,
    NULL AS taxa_anbima,
    NULL AS intervalo_min_d0,
    NULL AS intervalo_max_d0,
    NULL AS intervalo_min_d1,
    NULL AS intervalo_max_d1,
    NULL AS pu,
    NULL AS expressao_mercado,
    NULL AS data_base_mercado,
    NULL AS codigo_selic_mercado,
    NULL AS codigo_isin_mercado,
    NULL AS taxa_compra,
    NULL AS taxa_venda,
    NULL AS desvio_padrao,
    NULL AS status_mercado,
    l.qtd_operacoes,
    l.qtd_titulos,
    l.pu_medio AS pu_medio_liq,
    l.expressao AS expressao_liq,
    l.data_base AS data_base_liq,
    l.codigo_selic AS codigo_selic_liq,
    l.codigo_isin AS codigo_isin_liq,
    l.status AS status_liq
FROM LIQUIDACOES_MERCADO l
LEFT JOIN MERCADO_SECUNDARIO m
    ON m.tipo_titulo = l.tipo_titulo
   AND m.data_vencimento = l.data_vencimento
   AND m.data_referencia = l.data_referencia
WHERE m.tipo_titulo IS NULL

) AS combined
ORDER BY data_referencia, tipo_titulo, data_vencimento
