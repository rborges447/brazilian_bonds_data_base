from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from config.paths import PROJECT_ROOT
from config.settings import PathSettings, get_settings


def test_data_start_date_validation() -> None:
    with pytest.raises(ValueError, match="DATA_START_DATE"):
        PathSettings(data_start_date="not-a-date")  # type: ignore[arg-type]


def test_data_start_date_parses_iso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2025-06-15")
    paths = PathSettings()
    assert paths.data_start_date == date(2025, 6, 15)


def test_db_path_relative(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SQLITE_DB_PATH", raising=False)
    monkeypatch.setenv("SQLITE_DB_PATH", "custom/db.sqlite")
    settings = get_settings()
    assert settings.db_path == PROJECT_ROOT / "custom" / "db.sqlite"


def test_db_path_absolute(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    abs_db = tmp_path / "abs.db"
    monkeypatch.setenv("SQLITE_DB_PATH", str(abs_db))
    settings = get_settings()
    assert settings.db_path == abs_db


def test_bronze_silver_under_data_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_ROOT", "lake_data")
    settings = get_settings()
    assert settings.bronze_root == PROJECT_ROOT / "lake_data" / "raw"
    assert settings.silver_root == PROJECT_ROOT / "lake_data" / "silver"


def test_migrations_dir_points_to_repo_root() -> None:
    settings = get_settings()
    assert settings.migrations_dir == PROJECT_ROOT / "migrations"


def test_anbima_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANBIMA_CLIENT_ID", raising=False)
    monkeypatch.delenv("ANBIMA_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("ANBIMA_TIMEOUT", raising=False)
    monkeypatch.setenv("ANBIMA_CLIENT_ID", "id-test")
    monkeypatch.setenv("ANBIMA_CLIENT_SECRET", "secret-test")
    monkeypatch.setenv("ANBIMA_TIMEOUT", "45")
    settings = get_settings()
    assert settings.anbima.client_id == "id-test"
    assert settings.anbima.client_secret == "secret-test"
    assert settings.anbima.timeout == 45
