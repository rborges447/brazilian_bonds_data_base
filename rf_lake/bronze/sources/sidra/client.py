"""
Cliente para SIDRA (IBGE) via sidrapy.

Este client tem responsabilidade única: fazer a extração (rede) do IPCA mensal.
Transformações/normalizações ficam em `sources/sidra/mapping.py` e `etl/normalizers/`.
"""

from __future__ import annotations

import time

import pandas as pd

from rf_lake.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# Constantes obrigatórias (NÃO mudar sem motivo forte)
# ============================================================================

DEFAULT_PERIOD = "last 60"

VAR_IPCA_INDEX = "2266"  # número-índice
VAR_IPCA_MOM = "63"  # variação mensal (%)

TERRITORIAL_LEVEL_BR = "1"
IBGE_TERRITORIAL_CODE_BR = "1"

TABLE_CODE_IPCA = "6691"


class SidraIpcaClient:
    """
    Client de extração do IPCA mensal via SIDRA.

    Importante:
    - Todas as consultas usam SEMPRE `DEFAULT_PERIOD = "last 60"`.
    - Este client não normaliza/pivota dados; ele apenas chama sidrapy e retorna o DataFrame bruto.
    """

    def __init__(self, max_retries: int = 3):
        if max_retries <= 0:
            raise ValueError("max_retries deve ser >= 1")
        self.max_retries = int(max_retries)

    def fetch_table_ipca(self) -> pd.DataFrame:
        """
        Busca a tabela do IPCA no SIDRA (retorno bruto do sidrapy).

        Returns:
            DataFrame retornado pelo `sidrapy.get_table`.

        Raises:
            RuntimeError: se falhar após retries.
        """
        last_err: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                import sidrapy  # import local para facilitar testes e falhas controladas

                df = sidrapy.get_table(
                    table_code=TABLE_CODE_IPCA,
                    territorial_level=TERRITORIAL_LEVEL_BR,
                    ibge_territorial_code=IBGE_TERRITORIAL_CODE_BR,
                    period=DEFAULT_PERIOD,
                )

                if df is None:
                    return pd.DataFrame()

                if not isinstance(df, pd.DataFrame):
                    raise TypeError(f"SIDRA: retorno inesperado de sidrapy.get_table: {type(df)!r}")

                return df

            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    logger.warning("SIDRA: falha ao buscar IPCA (tentativa %s/%s): %s", attempt, self.max_retries, e)
                    time.sleep(0.6 * attempt)
                else:
                    break

        raise RuntimeError(f"SIDRA: falha ao buscar IPCA após {self.max_retries} tentativas: {last_err}") from last_err

