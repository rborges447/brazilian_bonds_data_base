"""Public entry point for bronze extraction."""

from __future__ import annotations

from app.contracts import ExtractResult
from app.lake.bronze.registry import extract_dataset as _extract_dataset

__all__ = ["extract_dataset"]


def extract_dataset(name: str, dates: list[str]) -> ExtractResult:
    return _extract_dataset(name, dates)
