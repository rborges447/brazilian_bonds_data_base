"""Public read entrypoint (facade over internal GoldReader)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.database.readers.gold_reader import GoldReader


def read_data(
    *,
    db_path: str | Path | None = None,
    data_root: str | Path | None = None,
    **kwargs: Any,
) -> GoldReader:
    """Return dataset-oriented accessor for curated gold tables."""
    if kwargs:
        raise TypeError(f"unexpected keyword arguments: {sorted(kwargs)}")
    if data_root is not None and db_path is None:
        from app.services.local_environment_service import ensure_local_environment

        env = ensure_local_environment(data_root, create=True)
        db_path = env.sqlite_db_path
    from app.database.readers import GoldReader

    return GoldReader(db_path=db_path)
