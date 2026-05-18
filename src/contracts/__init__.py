"""Layer contracts (types and protocols only — no I/O)."""

from contracts.bronze import BronzeExtractor, ExtractResult
from contracts.providers import (
    AnbimaFeedClient,
    DateRangeDataFrameFetcher,
    DateRangeRecordFetcher,
    SidraIpcaProvider,
    SnapshotDataFrameFetcher,
    SnapshotDateListFetcher,
)

__all__ = [
    "AnbimaFeedClient",
    "BronzeExtractor",
    "DateRangeDataFrameFetcher",
    "DateRangeRecordFetcher",
    "ExtractResult",
    "SidraIpcaProvider",
    "SnapshotDataFrameFetcher",
    "SnapshotDateListFetcher",
]
