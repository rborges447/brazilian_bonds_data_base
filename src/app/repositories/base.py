"""Repository protocol for gold SQL persistence."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class Repository(Protocol):
    """Persist tabular gold output; no business logic."""

    def upsert(self, df: pd.DataFrame) -> int:
        """Insert or replace rows; returns number of rows written."""
        ...
