"""Public entry point for bronze extraction."""

from __future__ import annotations

from contracts import ExtractResult
from pipelines.bronze.registry import extract_dataset as _extract_dataset

__all__ = ["extract_dataset"]


def extract_dataset(name: str, dates: list[str]) -> ExtractResult:
    return _extract_dataset(name, dates)
