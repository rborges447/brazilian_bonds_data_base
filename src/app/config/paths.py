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
