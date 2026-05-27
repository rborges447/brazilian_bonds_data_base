SELECT data_referencia, codigo_selic, tipo_correcao, "index", data_validade, vna, vna_ajustado
FROM VNA
WHERE data_referencia BETWEEN ? AND ?
ORDER BY data_referencia, codigo_selic
