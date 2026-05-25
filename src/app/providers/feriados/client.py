"""Client for national holidays (public ANBIMA XLS)."""

from __future__ import annotations

from io import BytesIO
from typing import List

import pandas as pd
import requests

from app.config import FeriadosSettings, get_settings


def fetch_feriados(settings: FeriadosSettings | None = None) -> List[str]:
    """
    Download national-holiday XLS and return dates as ISO strings YYYY-MM-DD.
    """
    cfg = settings or get_settings().feriados
    resp = requests.get(cfg.xls_url, timeout=cfg.timeout)
    resp.raise_for_status()

    feriados_df = pd.read_excel(BytesIO(resp.content))
    feriados_df.dropna(inplace=True)

    if "Data" not in feriados_df.columns:
        return []

    dates = pd.to_datetime(feriados_df["Data"])
    return [d.strftime("%Y-%m-%d") for d in dates.tolist()]
