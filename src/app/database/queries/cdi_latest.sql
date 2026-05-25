WITH latest_dates AS (
    SELECT data_referencia
    FROM CDI
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT data_referencia, cdi
FROM CDI
WHERE data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY data_referencia DESC
