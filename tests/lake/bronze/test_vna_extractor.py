from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.lake.bronze.extractors.vna import extract_vna
from app.lake.bronze.paths import bronze_partition_path

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


@patch("app.lake.bronze.extractors.vna.AnbimaClient")
def test_extract_vna_writes_partition_json(
    mock_client_cls: MagicMock, bronze_tmp_root
) -> None:
    mock_client = MagicMock()
    mock_client.fetch_vna.return_value = _VNA_PAYLOAD
    mock_client_cls.return_value = mock_client

    result = extract_vna([_REF_DATE])

    mock_client.fetch_vna.assert_called_once_with(_REF_DATE)
    path = bronze_partition_path("vna", "data", _REF_DATE, "json")
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8")) == _VNA_PAYLOAD
    assert result.segment_keys == [_REF_DATE]
    assert result.row_count == 1
    assert result.path == path


@patch("app.lake.bronze.extractors.vna.AnbimaClient")
def test_extract_vna_skips_when_fetch_returns_none(
    mock_client_cls: MagicMock, bronze_tmp_root
) -> None:
    mock_client = MagicMock()
    mock_client.fetch_vna.return_value = None
    mock_client_cls.return_value = mock_client

    result = extract_vna([_REF_DATE])

    path = bronze_partition_path("vna", "data", _REF_DATE, "json")
    assert not path.is_file()
    assert result.segment_keys == []
    assert result.row_count == 0
    assert result.path is None


@patch("app.lake.bronze.extractors.vna.AnbimaClient")
def test_extract_vna_idempotent_second_run(
    mock_client_cls: MagicMock, bronze_tmp_root
) -> None:
    mock_client = MagicMock()
    mock_client.fetch_vna.return_value = _VNA_PAYLOAD
    mock_client_cls.return_value = mock_client

    first = extract_vna([_REF_DATE])
    assert first.segment_keys == [_REF_DATE]

    second = extract_vna([_REF_DATE])
    assert second.segment_keys == []
    assert second.row_count == 0
    assert mock_client.fetch_vna.call_count == 1
