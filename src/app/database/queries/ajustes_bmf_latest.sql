WITH latest_dates AS (
    SELECT data_referencia
    FROM AJUSTES_BMF
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT ticker, data_referencia, taxa_ajuste, quantidade_ajuste
FROM AJUSTES_BMF
WHERE data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY data_referencia DESC, ticker
