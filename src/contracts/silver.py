"""Contracts for silver pipeline transforms and orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

import pandas as pd


@dataclass(frozen=True)
class SilverPartitionRef:
    """Reference to one hive partition artifact on disk (silver layer)."""

    dataset: str
    partition_key: str
    partition_value: str
    path: Path


SilverTransform: TypeAlias = Callable[
    [pd.DataFrame, str, list[str] | None],
    pd.DataFrame,
]
"""Normalize one bronze partition: (df_raw, partition_value, filter_dates)."""


@dataclass
class SilverResult:
    """Outcome of run_silver for one dataset."""

    name: str
    status: str  # success | skipped | error
    path: Path | None = None
    row_count: int = 0
    segment_keys: list[str] = field(default_factory=list)
    dates_candidate: list[str] = field(default_factory=list)
    error: str | None = None
