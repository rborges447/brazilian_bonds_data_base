from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from config import BcbSettings
from providers.bcb.ptax import (
    build_ptax_fechamento_url,
    fetch_ptax_fechamento,
    fetch_ptax_usd,
)

_SAMPLE_CSV = "20042026;220;A;USD;4,9838;4,9844;1,0000;1,0000\n"


def test_build_ptax_url_formats_dates() -> None:
    cfg = BcbSettings(
        ptax_base_url="https://ptax.bcb.gov.br/ptax_internet/consultaBoletim.do",
        ptax_moeda_code=61,
    )
    url = build_ptax_fechamento_url("2026-04-19", "2026-05-18", settings=cfg)
    assert "method=gerarCSVFechamentoMoedaNoPeriodo" in url
    assert "ChkMoeda=61" in url
    assert "DATAINI=19%2F04%2F2026" in url or "DATAINI=19/04/2026" in url
    assert "DATAFIM=18%2F05%2F2026" in url or "DATAFIM=18/05/2026" in url


@patch("providers.bcb.ptax.requests.get")
def test_fetch_ptax_parses_csv(mock_get: MagicMock) -> None:
    cfg = BcbSettings(max_retries=1)
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.apparent_encoding = "utf-8"
    response.text = _SAMPLE_CSV
    mock_get.return_value = response

    df = fetch_ptax_fechamento("2026-04-20", "2026-04-20", moeda_code=61, settings=cfg)

    assert len(df) == 1
    assert df["moeda"].iloc[0] == "USD"
    assert df["taxa_compra"].iloc[0] == pytest.approx(4.9838)
    assert df["taxa_venda"].iloc[0] == pytest.approx(4.9844)
    assert str(df["data"].iloc[0].date()) == "2026-04-20"


@patch("providers.bcb.ptax.requests.get")
def test_fetch_empty_returns_empty_df(mock_get: MagicMock) -> None:
    cfg = BcbSettings(max_retries=1)
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.apparent_encoding = "utf-8"
    response.text = ""
    mock_get.return_value = response

    df = fetch_ptax_fechamento("2026-04-20", "2026-04-20", settings=cfg)

    assert df.empty
    assert list(df.columns) == [
        "data",
        "codigo",
        "tipo",
        "moeda",
        "taxa_compra",
        "taxa_venda",
        "paridade_compra",
        "paridade_venda",
    ]


def test_csv_text_ignores_html_response() -> None:
    from providers.bcb.ptax import _csv_text_to_dataframe

    html = "<!DOCTYPE html><html><body>erro</body></html>"
    df = _csv_text_to_dataframe(html)
    assert df.empty


@patch("providers.bcb.ptax.requests.get")
def test_fetch_single_day_filters_to_requested_date(mock_get: MagicMock) -> None:
    cfg = BcbSettings(max_retries=1)
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.apparent_encoding = "utf-8"
    response.text = (
        "14052026;220;A;USD;4,9803;4,9809;1,0000;1,0000\n"
        "15052026;220;A;USD;5,0648;5,0654;1,0000;1,0000\n"
    )
    mock_get.return_value = response

    df = fetch_ptax_fechamento("2026-05-15", "2026-05-15", settings=cfg)

    assert len(df) == 1
    assert str(df["data"].iloc[0].date()) == "2026-05-15"
    assert "DATAINI" in mock_get.call_args[0][0]
    assert "DATAFIM=15%2F05%2F2026" in mock_get.call_args[0][0] or "DATAFIM=15/05/2026" in mock_get.call_args[0][0]


@patch("providers.bcb.ptax.fetch_ptax_fechamento")
def test_fetch_ptax_usd_uses_moeda_from_settings(mock_fetch: MagicMock) -> None:
    mock_fetch.return_value = pd.DataFrame(columns=["data"])
    cfg = BcbSettings(ptax_moeda_code=61)

    fetch_ptax_usd("2026-04-19", "2026-05-18", settings=cfg)

    mock_fetch.assert_called_once_with(
        start_date="2026-04-19",
        end_date="2026-05-18",
        moeda_code=61,
        settings=cfg,
    )
