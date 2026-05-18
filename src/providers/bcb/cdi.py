"""CDI daily rate from BCB SGS (series 11 by default)."""

from __future__ import annotations

import pandas as pd

from config import BcbSettings, get_settings
from providers.base import DateInput
from providers.bcb.sgs import fetch_bcb_sgs_series


def fetch_cdi_daily(
    start_date: DateInput | None = None,
    end_date: DateInput | None = None,
    settings: BcbSettings | None = None,
) -> pd.DataFrame:
    """Fetch CDI (% a.a., daily) from BCB SGS. Returns columns ``data`` and ``valor``."""
    cfg = settings or get_settings().bcb
    return fetch_bcb_sgs_series(
        series_id=cfg.cdi_series_id,
        start_date=start_date,
        end_date=end_date,
        settings=cfg,
    )
