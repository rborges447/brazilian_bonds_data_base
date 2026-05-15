"""
Client for national holidays (ANBIMA public XLS).
"""

from __future__ import annotations

from io import BytesIO
from typing import List

import pandas as pd
import requests

FERIADOS_XLS_URL = "https://www.anbima.com.br/feriados/arqs/feriados_nacionais.xls"


def fetch_feriados() -> List[str]:
    """
    Download ANBIMA national-holiday XLS and return
    dates as ISO strings "YYYY-MM-DD".

    Returns:
        List of "YYYY-MM-DD" strings.
    """
    resp = requests.get(FERIADOS_XLS_URL, timeout=30)
    resp.raise_for_status()

    feriados_df = pd.read_excel(BytesIO(resp.content))
    feriados_df.dropna(inplace=True)

    if "Data" not in feriados_df.columns:
        return []

    dates = pd.to_datetime(feriados_df["Data"])
    return [d.strftime("%Y-%m-%d") for d in dates.tolist()]
