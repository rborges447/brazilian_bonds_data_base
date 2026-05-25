"""IPCA facade — delegates to gold builder (no duplicated business rules)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.lake.gold.builders.ipca_dict import build_for_date


def build_ipca_dict_for_date(
    date: str,
    *,
    ipca_monthly: pd.DataFrame,
    projecoes: pd.DataFrame,
    feriados: set[str],
) -> dict[str, Any]:
    """Build one day's IPCA dict; same rules as ``lake.gold.builders.ipca_dict``."""
    return build_for_date(
        date,
        ipca_monthly=ipca_monthly,
        projecoes=projecoes,
        feriados=feriados,
    )
