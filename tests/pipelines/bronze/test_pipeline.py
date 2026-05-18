from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from contracts import ExtractResult
from models.dates import business_days
from pipelines.bronze.tasks import resolve_bronze_tasks
from pipelines.bronze.pipeline import run_bronze


def test_business_days_skips_weekends() -> None:
    days = business_days("2026-01-10", "2026-01-12")  # Sat–Mon
    assert days == ["2026-01-12"]


def test_resolve_bronze_tasks_missing_partitions(bronze_tmp_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-12")
    get_settings = __import__("config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    tasks = resolve_bronze_tasks("2026-01-12")
    ms = next(t for t in tasks if t.name == "mercado_secundario")
    assert "2026-01-12" in ms.dates
    proj = next(t for t in tasks if t.name == "projecoes")
    assert proj.dates == ["2026-01-01"]


@patch("pipelines.bronze.pipeline.extract_dataset")
def test_run_bronze_success(mock_extract, bronze_tmp_root) -> None:
    mock_extract.return_value = ExtractResult(
        path=bronze_tmp_root / "x.json",
        row_count=10,
        segment_keys=["2026-01-15"],
    )
    result = run_bronze("mercado_secundario", ["2026-01-15"])
    assert result.status == "success"
    assert result.row_count == 10


@patch("pipelines.bronze.pipeline.extract_dataset")
def test_run_bronze_skipped(mock_extract, bronze_tmp_root) -> None:
    mock_extract.return_value = ExtractResult(path=None, row_count=0, segment_keys=[])
    result = run_bronze("mercado_secundario", ["2026-01-15"])
    assert result.status == "skipped"
