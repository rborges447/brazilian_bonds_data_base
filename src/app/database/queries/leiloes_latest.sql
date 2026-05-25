WITH latest_dates AS (
    SELECT data_referencia
    FROM LEILOES
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT numero_edital, tipo_titulo, data_vencimento, data_referencia, oferta, quantidade_aceita, percentual_corte, oferta_segunda_volta, financeiro_aceito, financeiro_aceito_segunda_volta, quantidade_aceita_segunda_volta, pu_medio, taxa_media
FROM LEILOES
WHERE data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY data_referencia DESC, numero_edital, tipo_titulo, data_vencimento
