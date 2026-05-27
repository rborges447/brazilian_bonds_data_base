from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import AnbimaSettings
from app.providers.anbima.client import AnbimaClient

_REF_DATE = "2025-05-26"
_VNA_PAYLOAD = [
    {
        "data_referencia": _REF_DATE,
        "titulos": [
            {
                "tipo_titulo": "LFT",
                "codigo_selic": "210100",
                "index": 14.65,
                "tipo_correcao": "O",
                "data_validade": "2025-05-23",
                "vna": 16616.592308,
            }
        ],
    }
]


@pytest.fixture
def anbima_client() -> AnbimaClient:
    cfg = AnbimaSettings(client_id="cid", client_secret="secret")
    client = AnbimaClient(settings=cfg)
    client.auth = MagicMock()
    client.auth.build_headers.return_value = {"access_token": "t", "client_id": "cid"}
    return client


@patch.object(AnbimaClient, "fetch_by_date")
def test_fetch_vna_delegates_to_fetch_by_date(
    mock_fetch_by_date: MagicMock, anbima_client: AnbimaClient
) -> None:
    mock_fetch_by_date.return_value = _VNA_PAYLOAD
    result = anbima_client.fetch_vna(_REF_DATE)
    assert result == _VNA_PAYLOAD
    mock_fetch_by_date.assert_called_once_with(anbima_client.vna_url, _REF_DATE)


@patch("app.providers.anbima.client.requests.get")
def test_fetch_vna_http_success(
    mock_get: MagicMock, anbima_client: AnbimaClient
) -> None:
    mock_get.return_value = MagicMock(
        status_code=200,
        **{
            "json.return_value": _VNA_PAYLOAD,
            "raise_for_status.return_value": None,
        },
    )
    result = anbima_client.fetch_vna(_REF_DATE)
    assert result == _VNA_PAYLOAD
    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args.kwargs
    assert call_kwargs["params"] == {"data": _REF_DATE}
    assert mock_get.call_args.args[0] == anbima_client.vna_url


@patch("app.providers.anbima.client.requests.get")
def test_fetch_vna_http_404_returns_none(
    mock_get: MagicMock, anbima_client: AnbimaClient
) -> None:
    mock_get.return_value = MagicMock(status_code=404)
    assert anbima_client.fetch_vna(_REF_DATE) is None
