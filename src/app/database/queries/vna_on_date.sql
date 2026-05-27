SELECT data_referencia, codigo_selic, tipo_correcao, "index", data_validade, vna, vna_ajustado
FROM VNA
WHERE data_referencia = ?
ORDER BY data_referencia, codigo_selic
