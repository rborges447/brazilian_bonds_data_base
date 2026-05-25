from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.core.sync_verify import bronze_gaps, gold_gaps, silver_gaps, sync_status_report


def test_bronze_gaps_detects_missing_partition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DATA_START_DATE", "2026-01-15")
    from app.config import get_settings

    get_settings.cache_clear()
    gaps = bronze_gaps("cdi", "2026-01-15", "2026-01-15")
    assert "2026-01-15" in gaps


def test_silver_gaps_when_bronze_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    from app.lake.bronze.writer import write_partition_parquet

    monkeypatch.setenv("DATA_START_DATE", "2026-01-15")
    from app.config import get_settings

    get_settings.cache_clear()
    write_partition_parquet(
        "cdi",
        "data",
        "2026-01-15",
        pd.DataFrame({"data": ["2026-01-15"], "valor": [13.0]}),
    )
    gaps = silver_gaps("cdi", "2026-01-15", "2026-01-15")
    assert "2026-01-15" in gaps


def test_sync_status_report_structure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DATA_START_DATE", "2026-01-15")
    from app.config import get_settings

    get_settings.cache_clear()
    report = sync_status_report("2026-01-15", check_persist=False)
    assert set(report) == {"bronze", "silver", "gold"}


def test_gold_gaps_feriados_with_persist_check_does_not_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: TABLE_FERIADOS must be in scope for feriados gold_gaps."""
    db = tmp_path / "app.db"
    monkeypatch.setenv("SQLITE_DB_PATH", str(db))
    monkeypatch.setenv("DATA_START_DATE", "2026-01-15")
    from app.config import get_settings
    from app.database import apply_migrations

    get_settings.cache_clear()
    apply_migrations(db_path=db)
    gaps = gold_gaps("feriados", "2026-01-15", "2026-01-15", db_path=db, check_persist=True)
    assert isinstance(gaps, list)
