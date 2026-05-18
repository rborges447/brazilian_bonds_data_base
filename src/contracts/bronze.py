"""Contracts for bronze pipeline extractors (aligned with legacy extract.py)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias


@dataclass(frozen=True)
class ExtractResult:
    """Outcome of a bronze extract run for one dataset."""

    path: Path | None
    row_count: int
    segment_keys: list[str]
    """Hive partition values written (e.g. ISO dates, reference_month=YYYY-MM-01, snapshot=1)."""


BronzeExtractor: TypeAlias = Callable[[list[str]], ExtractResult]
"""Callable registered per dataset name; dates drive incremental pulls or snapshots."""
