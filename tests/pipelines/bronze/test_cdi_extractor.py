from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from pipelines.bronze.extractors.cdi import extract_cdi
from pipelines.bronze.paths import bronze_partition_path


@patch("pipelines.bronze.extractors.cdi.fetch_cdi_daily")
def test_extract_cdi_writes_partitions(mock_fetch, bronze_tmp_root: Path) -> None:
    mock_fetch.return_value = pd.DataFrame(
        {
            "data": pd.to_datetime(["2026-01-15", "2026-01-16"]),
            "valor": [13.65, 13.66],
        }
    )

    result = extract_cdi(["2026-01-15", "2026-01-16"])

    assert result.row_count == 2
    assert set(result.segment_keys) == {"2026-01-15", "2026-01-16"}
    mock_fetch.assert_called_once_with(start_date="2026-01-15", end_date="2026-01-16")

    for day in ("2026-01-15", "2026-01-16"):
        path = bronze_partition_path("cdi", "data", day, "parquet")
        assert path.is_file()
        df = pd.read_parquet(path)
        assert list(df.columns) == ["data", "valor"]
        assert len(df) == 1


@patch("pipelines.bronze.extractors.cdi.fetch_cdi_daily")
def test_extract_cdi_skips_existing_partitions(mock_fetch, bronze_tmp_root: Path) -> None:
    existing = bronze_partition_path("cdi", "data", "2026-01-15", "parquet")
    existing.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"data": ["2026-01-15"], "valor": [13.65]}).to_parquet(existing, index=False)

    mock_fetch.return_value = pd.DataFrame(
        {
            "data": pd.to_datetime(["2026-01-16"]),
            "valor": [13.66],
        }
    )

    result = extract_cdi(["2026-01-15", "2026-01-16"])

    assert result.segment_keys == ["2026-01-16"]
    mock_fetch.assert_called_once_with(start_date="2026-01-16", end_date="2026-01-16")


@patch("pipelines.bronze.extractors.cdi.fetch_cdi_daily")
def test_extract_cdi_empty_provider_response(mock_fetch, bronze_tmp_root: Path) -> None:
    mock_fetch.return_value = pd.DataFrame(columns=["data", "valor"])

    result = extract_cdi(["2026-01-15"])

    assert result.row_count == 0
    assert result.segment_keys == []
    assert result.path is None
