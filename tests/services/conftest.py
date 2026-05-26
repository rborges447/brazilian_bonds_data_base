from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import get_settings


@pytest.fixture
def lake_tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point bronze_root and silver_root at temporary directories."""
    raw = tmp_path / "raw"
    silver = tmp_path / "silver"
    raw.mkdir()
    silver.mkdir()
    db_parent = tmp_path / "database"
    db_parent.mkdir()
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.bronze_root == raw
    assert settings.silver_root == silver
    yield tmp_path
    get_settings.cache_clear()
