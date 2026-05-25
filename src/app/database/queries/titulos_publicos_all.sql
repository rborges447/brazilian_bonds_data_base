SELECT
    tipo_titulo,
    data_vencimento,
    expressao,
    data_base,
    codigo_selic,
    codigo_isin,
    status
FROM TITULOS_PUBLICOS
ORDER BY data_vencimento, tipo_titulo
