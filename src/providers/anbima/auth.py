"""OAuth2 authentication for the ANBIMA API."""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Optional

import requests

from config import AnbimaSettings, get_settings


@dataclass
class Token:
    access_token: str
    expires_at: float  # epoch seconds


class AnbimaAuth:
    """OAuth2 client credentials flow for ANBIMA."""

    def __init__(
        self,
        settings: AnbimaSettings | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: int | None = None,
    ) -> None:
        cfg = settings or get_settings().anbima
        self.token_url = cfg.token_url
        self.client_id = (client_id if client_id is not None else cfg.client_id).strip()
        self.client_secret = (client_secret if client_secret is not None else cfg.client_secret).strip()
        self.timeout = timeout if timeout is not None else cfg.timeout

        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "ANBIMA credentials missing. Set ANBIMA_CLIENT_ID and ANBIMA_CLIENT_SECRET."
            )

        self._token: Optional[Token] = None

    def _basic_auth_header(self) -> str:
        raw = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("utf-8")

    def get_access_token(self) -> str:
        if self._token and time.time() < (self._token.expires_at - 30):
            return self._token.access_token

        headers = {
            "Content-Type": "application/json",
            "Authorization": self._basic_auth_header(),
        }
        data = {"grant_type": "client_credentials"}

        resp = requests.post(self.token_url, headers=headers, json=data, timeout=self.timeout)
        resp.raise_for_status()

        payload = resp.json()
        access_token = payload["access_token"]
        expires_in = float(payload.get("expires_in", 1800))

        self._token = Token(access_token=access_token, expires_at=time.time() + expires_in)
        return access_token

    def build_headers(self) -> dict[str, str]:
        token = self.get_access_token()
        return {
            "Content-Type": "application/json",
            "client_id": self.client_id,
            "access_token": token,
        }
