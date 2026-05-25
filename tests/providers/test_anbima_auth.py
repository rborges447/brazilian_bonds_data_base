from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import AnbimaSettings
from app.providers.anbima.auth import AnbimaAuth


def test_anbima_auth_requires_credentials() -> None:
    cfg = AnbimaSettings(client_id="", client_secret="")
    with pytest.raises(RuntimeError, match="ANBIMA credentials missing"):
        AnbimaAuth(settings=cfg)


@patch("app.providers.anbima.auth.requests.post")
def test_anbima_auth_fetches_token(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        status_code=200,
        **{
            "json.return_value": {"access_token": "tok-abc", "expires_in": 3600},
            "raise_for_status.return_value": None,
        },
    )
    cfg = AnbimaSettings(client_id="cid", client_secret="csecret", timeout=10)
    auth = AnbimaAuth(settings=cfg)
    token = auth.get_access_token()
    assert token == "tok-abc"
    headers = auth.build_headers()
    assert headers["access_token"] == "tok-abc"
    assert headers["client_id"] == "cid"
    mock_post.assert_called_once()
