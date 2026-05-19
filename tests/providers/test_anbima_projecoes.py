from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from config.settings import AnbimaSettings
from providers.anbima.client import AnbimaClient


@pytest.fixture
def anbima_client() -> AnbimaClient:
    cfg = AnbimaSettings(client_id="cid", client_secret="secret")
    client = AnbimaClient(settings=cfg)
    client.auth = MagicMock()
    client.auth.build_headers.return_value = {"access_token": "t", "client_id": "cid"}
    return client


@patch("providers.anbima.client.requests.get")
def test_fetch_projecoes_latest_no_query_params(
    mock_get: MagicMock, anbima_client: AnbimaClient
) -> None:
    mock_get.return_value = MagicMock(
        status_code=200,
        **{"json.return_value": [{"indice": "IPCA"}], "raise_for_status.return_value": None},
    )
    result = anbima_client.fetch_projecoes_latest()
    assert result == [{"indice": "IPCA"}]
    mock_get.assert_called_once()
    assert "params" not in mock_get.call_args.kwargs or not mock_get.call_args.kwargs.get("params")


@patch("providers.anbima.client.requests.get")
def test_fetch_projecoes_latest_404_returns_none(
    mock_get: MagicMock, anbima_client: AnbimaClient
) -> None:
    mock_get.return_value = MagicMock(status_code=404)
    assert anbima_client.fetch_projecoes_latest() is None
