WITH latest_dates AS (
    SELECT data_referencia
    FROM LIQUIDACOES_MERCADO
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT tipo_titulo, data_vencimento, data_referencia, qtd_operacoes, qtd_titulos, pu_medio, expressao, data_base, codigo_selic, codigo_isin, status
FROM LIQUIDACOES_MERCADO
WHERE data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY data_referencia DESC, tipo_titulo, data_vencimento
