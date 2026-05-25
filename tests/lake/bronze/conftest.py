from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import get_settings


@pytest.fixture
def bronze_tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point bronze_root at a temporary directory."""
    raw = tmp_path / "raw"
    raw.mkdir()
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.bronze_root == raw
    yield raw
    get_settings.cache_clear()
