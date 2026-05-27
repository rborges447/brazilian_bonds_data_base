"""E2E: update(datasets=[vna]) + read_data().vna with mocked ANBIMA."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.database import MIGRATIONS_DIR, apply_migrations
from app.public import read_data, update
from app.services.local_environment_service import ensure_local_environment

_REF_DATE = "2026-05-20"
_VNA_PAYLOAD = [
    {
        "data_referencia": _REF_DATE,
        "titulos": [
            {
                "tipo_titulo": "LFT",
                "codigo_selic": "210100",
                "index": 14.65,
                "tipo_correcao": "O",
                "data_validade": "2026-05-19",
                "vna": 16616.592308,
            }
        ],
    }
]


@pytest.fixture(autouse=True)
def _data_start_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _setup_env(tmp_path: Path) -> Path:
    root = tmp_path / "pkg"
    env = ensure_local_environment(data_root=root, create=True)
    apply_migrations(db_path=env.sqlite_db_path, migrations_dir=MIGRATIONS_DIR)
    return root


@patch("app.lake.bronze.extractors.vna.AnbimaClient")
def test_update_vna_e2e(mock_client_cls: MagicMock, tmp_path: Path) -> None:
    mock_client = MagicMock()
    mock_client.fetch_vna.return_value = _VNA_PAYLOAD
    mock_client_cls.return_value = mock_client

    root = _setup_env(tmp_path)
    update(
        data_root=str(root),
        datasets=["vna"],
        start_date=_REF_DATE,
        end_date=_REF_DATE,
    )

    df = read_data(data_root=str(root)).vna.fetch_on(_REF_DATE)
    assert len(df) == 1
    assert int(df.iloc[0]["codigo_selic"]) == 210100
    assert float(df.iloc[0]["vna"]) == pytest.approx(16616.592308)
    assert df.iloc[0]["data_referencia"] == _REF_DATE
    mock_client.fetch_vna.assert_called_once_with(_REF_DATE)
