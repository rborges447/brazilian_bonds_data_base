"""Contracts for bronze pipeline extractors and orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class BronzePartitionRef:
    """Reference to one hive partition artifact on disk."""

    dataset: str
    partition_key: str
    partition_value: str
    path: Path


@dataclass
class BronzeResult:
    """Outcome of run_bronze for one dataset."""

    name: str
    status: str  # success | skipped | error
    path: Path | None = None
    row_count: int = 0
    segment_keys: list[str] = field(default_factory=list)
    dates_candidate: list[str] = field(default_factory=list)
    error: str | None = None
