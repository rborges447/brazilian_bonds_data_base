"""Client for National Treasury auction results API."""

from __future__ import annotations

import logging
import time
from datetime import date, datetime
from typing import List, Optional, Sequence, Union

import requests

from app.config import TesouroSettings, get_settings

logger = logging.getLogger(__name__)

DateInput = Union[str, date, datetime]


def to_dd_mm_yyyy(data: DateInput) -> str:
    if isinstance(data, (date, datetime)):
        return data.strftime("%d/%m/%Y")

    s = str(data).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue

    if len(s) == 10 and s[2] == "/" and s[5] == "/":
        return s

    raise ValueError(f"Invalid date for DD/MM/YYYY: {data!r}")


def get_resultados(
    dataleilao: Optional[DateInput] = None,
    titulo: Optional[str] = None,
    ano: Optional[int] = None,
    anoinicial: Optional[int] = None,
    timeout: int | None = None,
    settings: TesouroSettings | None = None,
) -> dict:
    cfg = settings or get_settings().tesouro
    timeout_val = timeout if timeout is not None else cfg.timeout
    url = f"{cfg.base_url}{cfg.resultados_path}"
    params: dict[str, str] = {}

    if dataleilao is not None:
        params["dataleilao"] = to_dd_mm_yyyy(dataleilao)
    if titulo is not None:
        params["titulo"] = titulo
    if ano is not None:
        params["ano"] = str(ano)
    if anoinicial is not None:
        params["anoinicial"] = str(anoinicial)

    response = requests.get(url, params=params, timeout=timeout_val)
    response.raise_for_status()
    return response.json()


def get_resultados_by_dates(
    dates: Sequence[DateInput],
    titulo: Optional[str] = None,
    timeout: int | None = None,
    settings: TesouroSettings | None = None,
) -> List[dict]:
    cfg = settings or get_settings().tesouro
    timeout_val = timeout if timeout is not None else cfg.timeout
    all_resultados: List[dict] = []

    def _year_from_date_input(d: DateInput) -> int:
        if isinstance(d, (date, datetime)):
            return int(d.year)
        s = str(d).strip()
        if len(s) >= 4 and s[:4].isdigit():
            return int(s[:4])
        dd = to_dd_mm_yyyy(s)
        return int(dd.split("/")[-1])

    years = sorted({_year_from_date_input(d) for d in dates})
    logger.info(
        "Treasury results API: fetching years=%s (requested_dates=%s)",
        years,
        len(dates),
    )

    for year in years:
        for attempt in range(1, cfg.max_retries + 1):
            try:
                response = get_resultados(
                    ano=year,
                    titulo=titulo,
                    timeout=timeout_val,
                    settings=cfg,
                )
                if isinstance(response, dict) and "registros" in response:
                    all_resultados.extend(response["registros"])
                break
            except requests.RequestException as exc:
                if attempt < cfg.max_retries:
                    time.sleep(0.6 * attempt)
                else:
                    logger.warning("Treasury results API: failed for year=%s: %s", year, exc)
                    break

    return all_resultados
