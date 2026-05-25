from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.lake.bronze.extractors._projecoes_split import (
    flatten_projecoes_payload,
    group_records_by_reference_month,
    load_partition_records,
    merge_projecoes_records,
    mes_referencia_to_partition_key,
    write_merged_partition,
)
from app.lake.bronze.extractors.projecoes import extract_projecoes
from app.lake.bronze.paths import bronze_partition_path


def _sample_records() -> list[dict]:
    return [
        {
            "indice": "IPCA",
            "tipo_projecao": "PROJEÇÕES PARA O MÊS CORRENTE",
            "data_coleta": "2026-05-12",
            "mes_referencia": "05/2026",
            "variacao_projetada": 0.5,
            "data_validade": "2026-05-18",
        },
        {
            "indice": "IPCA",
            "tipo_projecao": "PROJEÇÕES PARA O MÊS POSTERIOR",
            "data_coleta": "2026-05-12",
            "mes_referencia": "06/2026",
            "variacao_projetada": 0.33,
            "data_validade": None,
        },
    ]


def test_mes_referencia_to_partition_key_formats() -> None:
    assert mes_referencia_to_partition_key("05/2026") == "2026-05-01"
    assert mes_referencia_to_partition_key("05-2026") == "2026-05-01"
    assert mes_referencia_to_partition_key("2026-05-01") == "2026-05-01"


def test_group_records_splits_by_reference_month() -> None:
    grouped = group_records_by_reference_month(_sample_records())
    assert set(grouped) == {"2026-05-01", "2026-06-01"}
    assert len(grouped["2026-05-01"]) == 1
    assert len(grouped["2026-06-01"]) == 1


def test_merge_preserves_distinct_data_coleta() -> None:
    old = _sample_records()
    new = [
        {
            **old[0],
            "data_coleta": "2026-05-19",
            "variacao_projetada": 0.55,
        }
    ]
    merged = merge_projecoes_records(old, new)
    assert len(merged) == 3


def test_write_merged_partition_by_month(bronze_tmp_root: Path) -> None:
    grouped = group_records_by_reference_month(_sample_records())
    write_merged_partition("2026-05-01", grouped["2026-05-01"])
    write_merged_partition("2026-06-01", grouped["2026-06-01"])

    may_path = bronze_partition_path("projecoes", "reference_month", "2026-05-01", "json")
    june_path = bronze_partition_path("projecoes", "reference_month", "2026-06-01", "json")
    assert may_path.is_file()
    assert june_path.is_file()

    may_records = load_partition_records("2026-05-01")
    assert len(may_records) == 1
    assert may_records[0]["mes_referencia"] == "05/2026"

    june_records = json.loads(june_path.read_text(encoding="utf-8"))
    assert len(june_records) == 1
    assert june_records[0]["mes_referencia"] == "06/2026"


@patch("app.lake.bronze.extractors.projecoes.AnbimaClient")
def test_extract_projecoes_splits_partitions(
    mock_client_cls: MagicMock, bronze_tmp_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-05-01")
    get_settings = __import__("app.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    mock_client = mock_client_cls.return_value
    mock_client.fetch_projecoes_latest.return_value = None
    mock_client.fetch_projecoes.return_value = _sample_records()

    result = extract_projecoes(["2026-05-01"])
    assert "2026-05-01" in result.segment_keys
    assert "2026-06-01" in result.segment_keys
    assert load_partition_records("2026-06-01")
