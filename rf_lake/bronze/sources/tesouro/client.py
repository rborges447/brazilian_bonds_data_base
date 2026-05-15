"""
Client for National Treasury auction results API.
"""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import List, Optional, Sequence, Union

import requests

from rf_lake.logging import get_logger
from rf_lake.settings import TESOURO_MAX_RETRIES, TESOURO_TIMEOUT

logger = get_logger(__name__)

BASE_URL = "https://apiapex.tesouro.gov.br/aria"
RESULTADOS_PATH = "/v1/api-leiloes-pub/custom/resultados"


def to_dd_mm_yyyy(data: Union[str, date, datetime]) -> str:
    """
    Format a date as DD/MM/YYYY (expected by the API).

    Accepts:
    - YYYY-MM-DD (e.g. "2026-01-20")
    - DD/MM/YYYY (e.g. "20/01/2026")
    - date / datetime

    Args:
        data: Input date in any accepted form

    Returns:
        DD/MM/YYYY string

    Raises:
        ValueError: if the value cannot be parsed
    """
    if isinstance(data, (date, datetime)):
        return data.strftime("%d/%m/%Y")

    s = str(data).strip()
    from datetime import datetime as dt

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.strptime(s, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue

    if len(s) == 10 and s[2] == "/" and s[5] == "/":
        return s

    raise ValueError(f"Invalid date for DD/MM/YYYY: {data!r}")


#
# Portarias / editais flow was removed by product decision.
# Only the Results endpoint remains.
#


def get_resultados(
    dataleilao: Optional[Union[str, date, datetime]] = None,
    titulo: Optional[str] = None,
    ano: Optional[int] = None,
    anoinicial: Optional[int] = None,
    timeout: int = TESOURO_TIMEOUT
) -> dict:
    """
    Fetch Federal Public Debt auction results.

    All parameters are optional and can be combined.

    Args:
        dataleilao: Auction date YYYY-MM-DD (e.g. "2026-01-20") or DD/MM/YYYY.
                   When set, returns all results for that date.
        titulo: Bond code (e.g. "LTN", "NTN-B"). Filters to that bond when set.
        ano: Year (e.g. 2023). When set, returns all results for that year.
        anoinicial: Start year (e.g. 2015). When set, returns results from that year onward.
                   API default when omitted: 2015.
        timeout: HTTP timeout in seconds

    Returns:
        Dict with 'registros' (list of rows) and 'status'.

    Raises:
        requests.RequestException: on HTTP errors
        ValueError: if a date input cannot be converted
    """
    url = f"{BASE_URL}{RESULTADOS_PATH}"
    params = {}

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
    Fetch auction results for many dates and concatenate row lists.

    Robustness / performance note:
    - Treasury API supports lookup by YEAR (`ano`).
    - Instead of one request per date (often 500/504 on backfills),
      this derives distinct years from `dates` and issues one request per year.
    - The ETL layer filters to missing `data_referencia` values.

    Args:
        dates: List of dates YYYY-MM-DD (e.g. ["2026-01-20"])
        titulo: Bond filter (optional)
        timeout: HTTP timeout in seconds

    Returns:
        Concatenated list of all result rows
    """
    all_resultados: List[dict] = []

    def _year_from_date_input(d: Union[str, date, datetime]) -> int:
        if isinstance(d, (date, datetime)):
            return int(d.year)
        s = str(d).strip()
        if len(s) >= 4 and s[:4].isdigit():
            return int(s[:4])
        dd = to_dd_mm_yyyy(s)
        return int(dd.split("/")[-1])

    years = sorted({_year_from_date_input(d) for d in dates})
    logger.info(f"Tesouro results: fetching years={years} (requested_dates={len(dates)})")

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
                    logger.warning(f"Tesouro results: failed for year={year}: {e}")
                    break

    return all_resultados
