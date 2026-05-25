WITH latest_dates AS (
    SELECT data_referencia
    FROM PTAX
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT data_referencia, ptax_compra, ptax_venda
FROM PTAX
WHERE data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY data_referencia DESC
