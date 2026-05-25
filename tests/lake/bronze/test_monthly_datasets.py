from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.lake.bronze.tasks import resolve_bronze_tasks
from app.lake.bronze.extractors.ipca_indice import extract_ipca_indice
from app.lake.bronze.extractors.projecoes import _candidate_months


def test_resolve_bronze_tasks_monthly_from_data_start(
    bronze_tmp_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    get_settings = __import__("app.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    tasks = resolve_bronze_tasks("2026-05-15")
    proj = next(t for t in tasks if t.name == "projecoes")
    ipca = next(t for t in tasks if t.name == "ipca_indice")

    expected_proj = [
        "2026-01-01",
        "2026-02-01",
        "2026-03-01",
        "2026-04-01",
        "2026-05-01",
    ]
    expected_ipca = [
        "2025-09-01",
        "2025-10-01",
        "2025-11-01",
        "2025-12-01",
        *expected_proj,
    ]
    assert proj.dates == expected_proj
    assert ipca.dates == expected_ipca


def test_months_to_fetch_uses_task_dates() -> None:
    dates = ["2026-01-01", "2026-02-01", "2026-03-01"]
    assert _candidate_months(dates) == dates


@patch("app.lake.bronze.extractors.ipca_indice.write_partition_parquet")
@patch("app.lake.bronze.extractors.ipca_indice.SidraIpcaClient")
def test_extract_ipca_filters_before_data_start(
    mock_client_cls: MagicMock,
    mock_write: MagicMock,
    bronze_tmp_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-02-01")
    get_settings = __import__("app.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    df = pd.DataFrame(
        {
            "D2C": ["202601", "202602", "202603"],
            "V": [1.0, 2.0, 3.0],
        }
    )
    mock_client_cls.return_value.fetch_table_ipca.return_value = df
    mock_write.side_effect = lambda dataset, key, month, chunk, ext: (
        bronze_tmp_root / f"{month}.parquet"
    )

    result = extract_ipca_indice(
        ["2026-02-01", "2026-03-01"],
    )

    written_months = [call.args[2] for call in mock_write.call_args_list]
    assert "2026-01-01" not in written_months
    assert "2026-02-01" in written_months
    assert "2026-03-01" in written_months
    assert result.segment_keys == ["2026-02-01", "2026-03-01"]
