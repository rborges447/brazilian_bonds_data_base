WITH latest_dates AS (
    SELECT data_referencia
    FROM IPCA_DICT
    GROUP BY data_referencia
    ORDER BY data_referencia DESC
    LIMIT ?
)
SELECT data_referencia, ultimo_mes_ipca, ref_month_atual, ref_month_anterior, indice_ipca_data_base, indice_ipca_fechado_atual, indice_ipca_fechado_anterior, var_ipca_atual, var_ipca_ant, ipca_proj, ipca_usado, usa_fechado, data_coleta_referencia, ipca_proj_data_coleta, inicio_mes_ipca, fim_mes_ipca
FROM IPCA_DICT
WHERE data_referencia IN (SELECT data_referencia FROM latest_dates)
ORDER BY data_referencia DESC
