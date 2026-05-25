SELECT ticker, codigo_isin, data_vencimento
FROM CONTRATOS_BMF
ORDER BY ticker DESC
LIMIT ?
