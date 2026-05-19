"""HTTP client for the ANBIMA API."""

from __future__ import annotations

import time
from datetime import date
from typing import Any, List, Optional

import requests

from config import AnbimaSettings, get_settings
from providers.anbima.auth import AnbimaAuth

# Defaults aligned with AnbimaSettings (stable import-time constants)
MERCADO_SECUNDARIO_TPF = (
    "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/mercado-secundario-TPF"
)
VNA = "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/vna"
PROJECOES = "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/projecoes"


def _meses_anos_range(
    start_mes: int, start_ano: int, end_mes: int, end_ano: int
) -> List[tuple[int, int]]:
    out: List[tuple[int, int]] = []
    m, a = start_mes, start_ano
    while (a, m) <= (end_ano, end_mes):
        out.append((m, a))
        m += 1
        if m > 12:
            m = 1
            a += 1
    return out


class AnbimaClient:
    """HTTP client for ANBIMA market data."""

    def __init__(
        self,
        auth: AnbimaAuth | None = None,
        settings: AnbimaSettings | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        cfg = settings or get_settings().anbima
        self._settings = cfg
        self.auth = auth or AnbimaAuth(settings=cfg)
        self.timeout = timeout if timeout is not None else cfg.timeout
        self.max_retries = max_retries if max_retries is not None else cfg.max_retries
        self.mercado_secundario_tpf_url = cfg.mercado_secundario_tpf_url
        self.vna_url = cfg.vna_url
        self.projecoes_url = cfg.projecoes_url

    def fetch_by_date(self, url: str, date_iso: str) -> Optional[Any]:
        params = {"data": date_iso}
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                headers = self.auth.build_headers()
                resp = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_err = exc
                if attempt < self.max_retries:
                    time.sleep(0.6 * attempt)
                else:
                    raise last_err from None
        return None

    def fetch_by_mes_ano(self, url: str, mes: int | str, ano: int | str) -> Optional[Any]:
        params = {"mes": f"{int(mes):02d}", "ano": f"{int(ano):04d}"}
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                headers = self.auth.build_headers()
                resp = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_err = exc
                if attempt < self.max_retries:
                    time.sleep(0.6 * attempt)
                else:
                    raise last_err from None
        return None

    def fetch_projecoes(self, mes: int | str, ano: int | str) -> Optional[Any]:
        """
        Projections for a calendar month/year (IPCA and IGP-M).

        API fields: indice, tipo_projecao, data_coleta, mes_referencia (mm/aaaa),
        variacao_projetada, data_validade.
        """
        return self.fetch_by_mes_ano(self.projecoes_url, mes, ano)

    def fetch_projecoes_latest(self) -> Optional[Any]:
        """
        Latest available projections (no mes/ano query params).

        Per ANBIMA docs, returns the most recent month/year published when
        mes and ano are omitted.
        """
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                headers = self.auth.build_headers()
                resp = requests.get(
                    self.projecoes_url,
                    headers=headers,
                    timeout=self.timeout,
                )
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_err = exc
                if attempt < self.max_retries:
                    time.sleep(0.6 * attempt)
                else:
                    raise last_err from None
        return None

    def fetch_projecoes_historico(
        self,
        start_mes: int = 1,
        start_ano: int = 2024,
        end_mes: int | None = None,
        end_ano: int | None = None,
    ) -> List[Any]:
        today = date.today()
        em = end_mes if end_mes is not None else today.month
        ea = end_ano if end_ano is not None else today.year
        out: List[Any] = []
        for m, a in _meses_anos_range(start_mes, start_ano, em, ea):
            data = self.fetch_projecoes(m, a)
            if data is not None:
                out.append(data)
        return out

    def fetch_for_dates(self, url: str, date_list: List[str]) -> List[Any]:
        out: List[Any] = []
        for d in date_list:
            data = self.fetch_by_date(url, d)
            if data is not None:
                out.append(data)
        return out
