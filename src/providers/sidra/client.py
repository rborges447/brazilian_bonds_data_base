"""SIDRA (IBGE) client using sidrapy."""

from __future__ import annotations

import logging
import time

import pandas as pd

from config import SidraSettings, get_settings

logger = logging.getLogger(__name__)


class SidraIpcaClient:
    """
    IPCA monthly extraction client for SIDRA.
    Returns raw sidrapy DataFrame without normalization.
    """

    def __init__(self, settings: SidraSettings | None = None, max_retries: int | None = None) -> None:
        cfg = settings or get_settings().sidra
        self._settings = cfg
        retries = max_retries if max_retries is not None else cfg.max_retries
        if retries <= 0:
            raise ValueError("max_retries must be >= 1")
        self.max_retries = int(retries)

    def fetch_table_ipca(self) -> pd.DataFrame:
        cfg = self._settings
        last_err: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                import sidrapy

                df = sidrapy.get_table(
                    table_code=cfg.table_code_ipca,
                    territorial_level=cfg.territorial_level_br,
                    ibge_territorial_code=cfg.ibge_territorial_code_br,
                    period=cfg.default_period,
                )

                if df is None:
                    return pd.DataFrame()

                if not isinstance(df, pd.DataFrame):
                    raise TypeError(
                        f"SIDRA: unexpected sidrapy.get_table return type: {type(df)!r}"
                    )

                return df

            except Exception as exc:
                last_err = exc
                if attempt < self.max_retries:
                    logger.warning(
                        "SIDRA: IPCA fetch failed (attempt %s/%s): %s",
                        attempt,
                        self.max_retries,
                        exc,
                    )
                    time.sleep(0.6 * attempt)
                else:
                    break

        raise RuntimeError(
            f"SIDRA: IPCA fetch failed after {self.max_retries} attempts: {last_err}"
        ) from last_err
