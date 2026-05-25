"""Project root and path resolution."""

from __future__ import annotations

from pathlib import Path

# src/app/config/paths.py -> repo root
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def resolve_path(path: Path, base: Path = PROJECT_ROOT) -> Path:
    """Resolve relative paths against the project root."""
    if path.is_absolute():
        return path
    return base / path


def resolve_consumer_base(base: Path | None = None) -> Path:
    """Base directory for package consumer layout (default: current working directory)."""
    return Path.cwd() if base is None else base


def resolve_package_data_root(
    data_root: str | Path | None,
    *,
    base: Path | None = None,
) -> Path:
    """Resolve package data root: None -> base + PACKAGE_DATA_ROOT from settings; relative -> base/...; absolute -> as-is."""
    root_base = resolve_consumer_base(base)
    if data_root is None:
        from app.config import get_settings

        default = get_settings().paths.package_data_root
        return resolve_path(default, root_base)
    path = Path(data_root)
    if path.is_absolute():
        return path
    return root_base / path
