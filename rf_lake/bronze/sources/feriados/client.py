"""
Cliente para feriados nacionais (fonte ANBIMA – XLS público).
"""

from __future__ import annotations

from io import BytesIO
from typing import List

import pandas as pd
import requests

FERIADOS_XLS_URL = "https://www.anbima.com.br/feriados/arqs/feriados_nacionais.xls"


def fetch_feriados() -> List[str]:
    """
    Baixa o arquivo XLS de feriados nacionais da ANBIMA e retorna
    as datas em formato ISO "YYYY-MM-DD".

    Returns:
        Lista de strings no formato "YYYY-MM-DD".
    """
    resp = requests.get(FERIADOS_XLS_URL, timeout=30)
    resp.raise_for_status()

    feriados_df = pd.read_excel(BytesIO(resp.content))
    feriados_df.dropna(inplace=True)

    if "Data" not in feriados_df.columns:
        return []

    dates = pd.to_datetime(feriados_df["Data"])
    return [d.strftime("%Y-%m-%d") for d in dates.tolist()]
