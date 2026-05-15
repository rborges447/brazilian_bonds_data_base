"""Bootstrap: diretórios de dados + migrations SQLite."""

from __future__ import annotations

from rf_lake.gold.db import apply_migrations
from rf_lake.settings import ensure_data_layout
from rf_lake.watermarks import WATERMARKS_PATH, rebuild_watermarks_from_disk


def bootstrap(*, rebuild_watermarks: bool = False) -> None:
    ensure_data_layout()
    apply_migrations()
    if rebuild_watermarks or not WATERMARKS_PATH.is_file():
        rebuild_watermarks_from_disk()
