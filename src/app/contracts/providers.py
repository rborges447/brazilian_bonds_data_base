"""Contracts for raw data providers (fetch patterns, not a single mega-Protocol)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol, TypeAlias, runtime_checkable

import pandas as pd

DateRangeDataFrameFetcher: TypeAlias = Callable[[Sequence[str]], pd.DataFrame]
"""Fetch rows for many reference dates; returns a raw DataFrame (BCB, UpToData)."""

SnapshotDataFrameFetcher: TypeAlias = Callable[[], pd.DataFrame]
"""Snapshot pull with no date list (SIDRA IPCA table)."""

SnapshotDateListFetcher: TypeAlias = Callable[[], list[str]]
"""Snapshot list of ISO date strings (national holidays)."""

DateRangeRecordFetcher: TypeAlias = Callable[[Sequence[str]], list[dict]]
"""Fetch records for many dates before canonical mapping (Tesouro leilões)."""


@runtime_checkable
class SidraIpcaProvider(Protocol):
    def fetch_table_ipca(self) -> pd.DataFrame: ...


@runtime_checkable
class AnbimaFeedClient(Protocol):
    def fetch_by_date(self, url: str, date_iso: str) -> Any | None: ...

    def fetch_for_dates(self, url: str, date_list: list[str]) -> list[Any]: ...
