"""
Cliente para API de Leilões do Tesouro Nacional.
"""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import List, Optional, Sequence, Union

import requests

from rf_lake.logging import get_logger
from rf_lake.settings import TESOURO_MAX_RETRIES, TESOURO_TIMEOUT

logger = get_logger(__name__)

# Constantes de paths
BASE_URL = "https://apiapex.tesouro.gov.br/aria"
RESULTADOS_PATH = "/v1/api-leiloes-pub/custom/resultados"


def to_dd_mm_yyyy(data: Union[str, date, datetime]) -> str:
    """
    Converte data para formato DD/MM/YYYY (formato esperado pela API).
    
    Aceita:
    - YYYY-MM-DD (ex: "2026-01-20")
    - DD/MM/YYYY (ex: "20/01/2026")
    - date/datetime objects
    
    Args:
        data: Data em qualquer formato aceito
        
    Returns:
        String no formato DD/MM/YYYY
        
    Raises:
        ValueError: Se a data não puder ser convertida
    """
    if isinstance(data, (date, datetime)):
        return data.strftime("%d/%m/%Y")
    
    s = str(data).strip()
    from datetime import datetime as dt
    
    # Tenta diferentes formatos
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.strptime(s, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    
    # Se já está no formato correto, retorna direto
    if len(s) == 10 and s[2] == "/" and s[5] == "/":
        return s
    
    raise ValueError(f"Data inválida para DD/MM/YYYY: {data!r}")


#
# Nota: o fluxo de Portarias/Editais foi removido do projeto por decisão de produto.
# Mantemos apenas o endpoint de Resultados.
#


def get_resultados(
    dataleilao: Optional[Union[str, date, datetime]] = None,
    titulo: Optional[str] = None,
    ano: Optional[int] = None,
    anoinicial: Optional[int] = None,
    timeout: int = TESOURO_TIMEOUT
) -> dict:
    """
    Busca resultados de leilões da Dívida Pública Federal.
    
    Todos os parâmetros são opcionais e podem ser livremente combinados.
    
    Args:
        dataleilao: Data do leilão no formato YYYY-MM-DD (ex: "2026-01-20") ou DD/MM/YYYY.
                   Quando informado, retorna todos os resultados para a data informada.
        titulo: Título desejado (ex: "LTN", "NTN-B"). Quando informado, filtra os resultados
                apenas para o título informado.
        ano: Ano desejado (ex: 2023). Quando informado, retorna todos os resultados para o ano informado.
        anoinicial: Ano inicial desejado (ex: 2015). Quando informado, retorna todos os resultados
                   a partir do ano informado. Valor padrão da API: 2015.
        timeout: Timeout da requisição em segundos
        
    Returns:
        Dict com 'registros' (lista de resultados) e 'status'.
        Cada registro contém campos como: numero_edital, vencimento, quantidade_aceita,
        percentual_corte, quantidade_liquidada, taxa_maxima, taxa_media, tipo_leilao,
        data_leilao, prazo, financeiro_aceito, benchmark, oferta, titulo, quantidade_bcb,
        financeiro_bcb, liquidacao, liquidacao_segunda_volta, oferta_segunda_volta,
        pu_medio, pu_minimo, quantidade_aceita_segunda_volta, quantidade_liquidada_segunda_volta,
        financeiro_aceito_segunda_volta.
        
    Raises:
        requests.RequestException: Se houver erro na requisição
        ValueError: Se a data não puder ser convertida
    """
    url = f"{BASE_URL}{RESULTADOS_PATH}"
    params = {}
    
    # Adiciona parâmetros opcionais apenas se fornecidos
    if dataleilao is not None:
        params["dataleilao"] = to_dd_mm_yyyy(dataleilao)
    
    if titulo is not None:
        params["titulo"] = titulo
    
    if ano is not None:
        params["ano"] = str(ano)
    
    if anoinicial is not None:
        params["anoinicial"] = str(anoinicial)
    
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    
    return response.json()


def get_resultados_by_dates(
    dates: Sequence[Union[str, date, datetime]],
    titulo: Optional[str] = None,
    timeout: int = TESOURO_TIMEOUT
) -> List[dict]:
    """
    Busca resultados de leilões para múltiplas datas e retorna resultados concatenados.

    IMPORTANTE (estratégia de robustez/performance):
    - A API do Tesouro suporta consulta por ANO (parâmetro `ano`).
    - Em vez de fazer 1 request por data (que tende a gerar 500/504/timeouts em backfills),
      este método deriva os anos a partir de `dates` e faz 1 request por ano.
    - O pipeline ETL é responsável por filtrar apenas as `data_referencia` faltantes.
    
    Args:
        dates: Lista de datas no formato YYYY-MM-DD (ex: ["2026-01-20", "2026-01-21"])
        titulo: Título desejado (opcional). Se fornecido, filtra resultados apenas para este título.
        timeout: Timeout da requisição em segundos
        
    Returns:
        Lista concatenada de todos os resultados encontrados
    """
    all_resultados: List[dict] = []

    def _year_from_date_input(d: Union[str, date, datetime]) -> int:
        if isinstance(d, (date, datetime)):
            return int(d.year)
        s = str(d).strip()
        # happy path: YYYY-MM-DD (como o job gera)
        if len(s) >= 4 and s[:4].isdigit():
            return int(s[:4])
        # fallback: tentar converter para DD/MM/YYYY e extrair ano
        dd = to_dd_mm_yyyy(s)
        return int(dd.split("/")[-1])

    years = sorted({_year_from_date_input(d) for d in dates})
    logger.info(f"Tesouro resultados: buscando por anos={years} (datas_solicitadas={len(dates)})")

    for year in years:
        last_err: Optional[Exception] = None
        for attempt in range(1, TESOURO_MAX_RETRIES + 1):
            try:
                response = get_resultados(ano=year, titulo=titulo, timeout=timeout)
                if isinstance(response, dict) and "registros" in response:
                    all_resultados.extend(response["registros"])
                break
            except requests.RequestException as e:
                last_err = e
                if attempt < TESOURO_MAX_RETRIES:
                    time.sleep(0.6 * attempt)
                else:
                    logger.warning(f"Tesouro resultados: falha ao buscar ano={year}: {e}")
                    break
    
    return all_resultados
