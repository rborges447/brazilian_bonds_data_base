"""Resolve and create local package data layout for external consumers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.config.paths import resolve_package_data_root


@dataclass(frozen=True)
class LocalEnvironment:
    data_root: Path
    database_dir: Path
    sqlite_db_path: Path
    lake_root: Path
    bronze_root: Path
    silver_root: Path
    gold_root: Path
    logs_dir: Path
    metadata_dir: Path


def _build_environment(data_root: Path) -> LocalEnvironment:
    sqlite_db_path = data_root / get_settings().paths.package_sqlite_path
    database_dir = sqlite_db_path.parent
    lake_root = data_root / "lake"
    return LocalEnvironment(
        data_root=data_root,
        database_dir=database_dir,
        sqlite_db_path=sqlite_db_path,
        lake_root=lake_root,
        bronze_root=lake_root / "bronze",
        silver_root=lake_root / "silver",
        gold_root=lake_root / "gold",
        logs_dir=data_root / "logs",
        metadata_dir=data_root / "metadata",
    )


def _directories_to_create(env: LocalEnvironment) -> tuple[Path, ...]:
    return (
        env.data_root,
        env.database_dir,
        env.lake_root,
        env.bronze_root,
        env.silver_root,
        env.gold_root,
        env.logs_dir,
        env.metadata_dir,
        env.sqlite_db_path.parent,
    )


def ensure_local_environment(
    data_root: str | Path | None = None,
    *,
    base: Path | None = None,
    create: bool = True,
) -> LocalEnvironment:
    """Resolve package paths and optionally create the directory layout."""
    resolved_root = resolve_package_data_root(data_root, base=base)
    env = _build_environment(resolved_root)
    if create:
        for path in _directories_to_create(env):
            path.mkdir(parents=True, exist_ok=True)
    return env
