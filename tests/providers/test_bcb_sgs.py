from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from config import BcbSettings
from providers.bcb.cdi import fetch_cdi_daily
from providers.bcb.sgs import (
    _split_period_in_10y_chunks,
    build_sgs_url,
    fetch_bcb_sgs_series,
)


def test_build_sgs_url_formats_dates() -> None:
    cfg = BcbSettings(sgs_base_url="https://api.bcb.gov.br/dados/serie/bcdata.sgs")
    url = build_sgs_url(11, "2010-01-01", "2010-01-31", settings=cfg)
    assert "dataInicial=01/01/2010" in url
    assert "dataFinal=31/01/2010" in url
    assert url.endswith("/dados?formato=json&dataInicial=01/01/2010&dataFinal=31/01/2010") or (
        "bcdata.sgs.11/dados" in url
    )


def test_split_period_in_10y_chunks_long_range() -> None:
    start = date(2010, 1, 1)
    end = date(2025, 6, 15)
    chunks = _split_period_in_10y_chunks(start, end)
    assert len(chunks) >= 2
    assert chunks[0][0] == start
    assert chunks[-1][1] == end
    for i in range(len(chunks) - 1):
        assert chunks[i][1] + timedelta(days=1) == chunks[i + 1][0]
    # contiguous coverage
    assert chunks[0][0] == start
    assert chunks[-1][1] == end


def test_split_period_in_10y_chunks_rejects_inverted_range() -> None:
    with pytest.raises(ValueError, match="start date cannot be after end date"):
        _split_period_in_10y_chunks(date(2025, 1, 1), date(2020, 1, 1))


@patch("providers.bcb.sgs.requests.get")
def test_fetch_bcb_sgs_series_merges_chunks(mock_get: MagicMock) -> None:
    cfg = BcbSettings(
        sgs_base_url="https://api.bcb.gov.br/dados/serie/bcdata.sgs",
        timeout=5,
        max_retries=1,
    )

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = [
        {"data": "01/01/2020", "valor": "0.03"},
        {"data": "02/01/2020", "valor": "0.04"},
    ]
    mock_get.return_value = response

    df = fetch_bcb_sgs_series(11, "2020-01-01", "2020-01-02", settings=cfg)

    assert len(df) == 2
    assert list(df.columns) == ["data", "valor"]
    assert df["valor"].iloc[0] == pytest.approx(0.03)
    mock_get.assert_called()


@patch("providers.bcb.sgs.requests.get")
def test_fetch_empty_range_returns_empty_df(mock_get: MagicMock) -> None:
    cfg = BcbSettings(max_retries=1)
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = []
    mock_get.return_value = response

    df = fetch_bcb_sgs_series(11, "2020-01-01", "2020-01-02", settings=cfg)

    assert df.empty
    assert list(df.columns) == ["data", "valor"]


@patch("providers.bcb.cdi.fetch_bcb_sgs_series")
def test_fetch_cdi_daily_uses_series_from_settings(mock_fetch: MagicMock) -> None:
    mock_fetch.return_value = pd.DataFrame(columns=["data", "valor"])
    cfg = BcbSettings(cdi_series_id=11)

    fetch_cdi_daily("2020-01-01", "2020-01-02", settings=cfg)

    mock_fetch.assert_called_once_with(
        series_id=11,
        start_date="2020-01-01",
        end_date="2020-01-02",
        settings=cfg,
    )
