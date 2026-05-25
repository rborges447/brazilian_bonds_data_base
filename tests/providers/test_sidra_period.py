from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.providers.sidra.period import sidra_period_for_sync, sidra_period_from_dates


def test_sidra_period_from_dates_counts_months() -> None:
    assert sidra_period_from_dates(date(2026, 1, 1), date(2026, 3, 31)) == "last 3"
    assert sidra_period_from_dates(date(2026, 5, 1), date(2026, 5, 31)) == "last 2"


def test_sidra_client_uses_computed_period_when_env_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    monkeypatch.setenv("SIDRA_DEFAULT_PERIOD", "")
    from app.config import get_settings

    get_settings.cache_clear()

    captured: list[str] = []

    def fake_get_table(**kwargs):
        captured.append(kwargs["period"])
        return pd.DataFrame({"D2C": ["202601"], "V": [1]})

    mock_sidrapy = MagicMock()
    mock_sidrapy.get_table = fake_get_table

    with patch.dict("sys.modules", {"sidrapy": mock_sidrapy}):
        from app.providers.sidra.client import SidraIpcaClient

        client = SidraIpcaClient()
        client.fetch_table_ipca()

    assert captured
    assert captured[0].startswith("last ")
    assert int(captured[0].split()[-1]) >= 2


def test_sidra_period_for_sync_anchors_on_data_start_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    from app.core.dates import months_in_range
    from app.core.sync_range import sync_end_date, sync_ipca_month_start

    period = sidra_period_for_sync()
    assert period.startswith("last ")
    n = int(period.split()[-1])
    months_span = len(months_in_range(sync_ipca_month_start(), sync_end_date()))
    assert n == max(months_span, 2)
