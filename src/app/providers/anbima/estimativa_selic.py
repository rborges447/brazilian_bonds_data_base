"""ANBIMA daily SELIC rate estimate feed."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.config import AnbimaSettings, get_settings
from app.providers.anbima.client import AnbimaClient

_COLUMNS = ["data_referencia", "estimativa_taxa_selic"]


def _payload_to_records(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def fetch_estimativa_selic(
    date_iso: str | None = None,
    client: AnbimaClient | None = None,
    settings: AnbimaSettings | None = None,
) -> pd.DataFrame:
    """
    Fetch ANBIMA SELIC estimate. Returns ``data_referencia`` and
    ``estimativa_taxa_selic`` (% a.a./252).
    """
    cfg = settings or get_settings().anbima
    api = client or AnbimaClient(settings=cfg)
    payload = api.fetch_estimativa_selic(date_iso)
    records = _payload_to_records(payload)
    if not records:
        return pd.DataFrame(columns=_COLUMNS)
    df = pd.DataFrame(records)
    for col in _COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[_COLUMNS].copy()
    if "data_referencia" in df.columns:
        df["data_referencia"] = pd.to_datetime(df["data_referencia"], errors="coerce")
    if "estimativa_taxa_selic" in df.columns:
        df["estimativa_taxa_selic"] = pd.to_numeric(
            df["estimativa_taxa_selic"], errors="coerce"
        )
    return df
