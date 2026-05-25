from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import get_settings


@pytest.fixture
def lake_tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temporary data root with raw (bronze) and silver directories."""
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()
    settings = get_settings()
    settings.ensure_data_layout()
    yield tmp_path
    get_settings.cache_clear()
