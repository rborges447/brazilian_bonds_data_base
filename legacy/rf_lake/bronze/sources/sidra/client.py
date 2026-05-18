"""
SIDRA (IBGE) client using sidrapy.

This module only performs network extraction of monthly IPCA.
Transforms live in `sources/sidra/mapping.py` and Silver normalizers.
"""

from __future__ import annotations

import time

import pandas as pd

from rf_lake.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants (do not change without strong justification)
# ---------------------------------------------------------------------------

DEFAULT_PERIOD = "last 60"

VAR_IPCA_INDEX = "2266"  # index level
VAR_IPCA_MOM = "63"  # month-on-month (%)

TERRITORIAL_LEVEL_BR = "1"
IBGE_TERRITORIAL_CODE_BR = "1"

TABLE_CODE_IPCA = "6691"


class SidraIpcaClient:
    """
    IPCA monthly extraction client for SIDRA.

    Notes:
    - All calls use `DEFAULT_PERIOD = "last 60"`.
    - This client does not pivot or normalize; it returns the raw sidrapy DataFrame.
    """

    def __init__(self, max_retries: int = 3):
        if max_retries <= 0:
            raise ValueError("max_retries must be >= 1")
        self.max_retries = int(max_retries)

    def fetch_table_ipca(self) -> pd.DataFrame:
        """
        Fetch IPCA table from SIDRA (raw sidrapy output).

        Returns:
            DataFrame from `sidrapy.get_table`.

        Raises:
            RuntimeError: if all retries fail.
        """
        last_err: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                import sidrapy  # local import for tests and controlled failures

                df = sidrapy.get_table(
                    table_code=TABLE_CODE_IPCA,
                    territorial_level=TERRITORIAL_LEVEL_BR,
                    ibge_territorial_code=IBGE_TERRITORIAL_CODE_BR,
                    period=DEFAULT_PERIOD,
                )

                if df is None:
                    return pd.DataFrame()

                if not isinstance(df, pd.DataFrame):
                    raise TypeError(f"SIDRA: unexpected sidrapy.get_table return type: {type(df)!r}")

                return df

            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    logger.warning("SIDRA: IPCA fetch failed (attempt %s/%s): %s", attempt, self.max_retries, e)
                    time.sleep(0.6 * attempt)
                else:
                    break

        raise RuntimeError(f"SIDRA: IPCA fetch failed after {self.max_retries} attempts: {last_err}") from last_err
