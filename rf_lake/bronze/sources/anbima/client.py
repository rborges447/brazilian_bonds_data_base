"""
Cliente para API ANBIMA.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

import requests

from rf_lake.settings import ANBIMA_CLIENT_ID, ANBIMA_CLIENT_SECRET, ANBIMA_TIMEOUT, ANBIMA_MAX_RETRIES


@dataclass
class Token:
    access_token: str
    expires_at: float  # epoch seconds


class AnbimaAuth:
    """Autenticação OAuth2 para API ANBIMA."""
    
    TOKEN_URL = "https://api.anbima.com.br/oauth/access-token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        timeout: int = ANBIMA_TIMEOUT,
    ):
        self.client_id = (client_id or ANBIMA_CLIENT_ID).strip()
        self.client_secret = (client_secret or ANBIMA_CLIENT_SECRET).strip()
        self.timeout = timeout

        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "Credenciais ANBIMA ausentes. Defina ANBIMA_CLIENT_ID e ANBIMA_CLIENT_SECRET."
            )

        self._token: Optional[Token] = None

    def _basic_auth_header(self) -> str:
        raw = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("utf-8")

    def get_access_token(self) -> str:
        # reusa token se ainda válido
        if self._token and time.time() < (self._token.expires_at - 30):
            return self._token.access_token

        headers = {
            "Content-Type": "application/json",
            "Authorization": self._basic_auth_header(),
        }
        data = {"grant_type": "client_credentials"}

        resp = requests.post(self.TOKEN_URL, headers=headers, json=data, timeout=self.timeout)
        resp.raise_for_status()

        payload = resp.json()
        access_token = payload["access_token"]
        expires_in = float(payload.get("expires_in", 1800))  # fallback 30 min

        self._token = Token(access_token=access_token, expires_at=time.time() + expires_in)
        return access_token

    def build_headers(self) -> Dict[str, str]:
        token = self.get_access_token()

        return {
            "Content-Type": "application/json",
            "client_id": self.client_id,
            "access_token": token,
        }


# Endpoints da API ANBIMA
MERCADO_SECUNDARIO_TPF = "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/mercado-secundario-TPF"
VNA = "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/vna"
PROJECOES = "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/projecoes"


def _meses_anos_range(
    start_mes: int, start_ano: int, end_mes: int, end_ano: int
) -> List[tuple[int, int]]:
    """Gera lista de (mes, ano) do início ao fim (inclusive), em ordem cronológica."""
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
    """Cliente para buscar dados da API ANBIMA."""
    
    def __init__(self, auth: Optional[AnbimaAuth] = None, timeout: int = ANBIMA_TIMEOUT, max_retries: int = ANBIMA_MAX_RETRIES):
        self.auth = auth or AnbimaAuth()
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch_by_date(self, url: str, date_iso: str) -> Optional[Any]:
        """
        GET em um endpoint ANBIMA com params {'data': YYYY-MM-DD}
        Retorna JSON ou None se 404.
        """
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

            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(0.6 * attempt)
                else:
                    raise last_err from None

        return None

    def fetch_by_mes_ano(self, url: str, mes: int | str, ano: int | str) -> Optional[Any]:
        """
        GET em um endpoint ANBIMA com params {'mes': MM, 'ano': YYYY}.
        Retorna JSON ou None se 404.
        """
        mes_norm = f"{int(mes):02d}"
        ano_norm = f"{int(ano):04d}"
        params = {"mes": mes_norm, "ano": ano_norm}

        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                headers = self.auth.build_headers()
                resp = requests.get(url, headers=headers, params=params, timeout=self.timeout)

                if resp.status_code == 404:
                    return None

                resp.raise_for_status()
                return resp.json()

            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(0.6 * attempt)
                else:
                    raise last_err from None

        return None

    def fetch_projecoes(self, mes: int | str, ano: int | str) -> Optional[Any]:
        """
        Projeções IPCA/IGP-M para o mês/ano.
        Campos conforme doc: indice, tipo_projecao, data_coleta, mes_referencia, variacao_projetada, data_validade.
        """
        return self.fetch_by_mes_ano(PROJECOES, mes, ano)

    def fetch_projecoes_historico(
        self,
        start_mes: int = 1,
        start_ano: int = 2024,
        end_mes: Optional[int] = None,
        end_ano: Optional[int] = None,
    ) -> List[Any]:
        """
        Histórico de projeções de start_mes/start_ano até end_mes/end_ano (ou até hoje).
        Útil para backfill ou análises.
        """
        today = date.today()
        em = end_mes if end_mes is not None else today.month
        ea = end_ano if end_ano is not None else today.year
        meses_anos = _meses_anos_range(start_mes, start_ano, em, ea)
        out: List[Any] = []
        for m, a in meses_anos:
            data = self.fetch_projecoes(m, a)
            if data is not None:
                out.append(data)
        return out

    def fetch_for_dates(self, url: str, date_list: List[str]) -> List[Any]:
        """
        Loop em várias datas; retorna lista de JSONs (ignorando None).
        """
        out: List[Any] = []
        for d in date_list:
            data = self.fetch_by_date(url, d)
            if data is not None:
                out.append(data)
        return out
