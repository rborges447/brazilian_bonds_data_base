WITH latest_dates AS (
    SELECT data_referencia
    FROM VNA
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT data_referencia, codigo_selic, tipo_correcao, "index", data_validade, vna, vna_ajustado
FROM VNA
WHERE data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY data_referencia DESC, codigo_selic
