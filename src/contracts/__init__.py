"""Layer contracts (types and protocols only — no I/O)."""

from contracts.bronze import (
    BronzeExtractor,
    BronzePartitionRef,
    BronzeResult,
    ExtractResult,
)
from contracts.silver import SilverPartitionRef, SilverResult, SilverTransform
from contracts.providers import (
    AnbimaFeedClient,
    DateRangeDataFrameFetcher,
    DateRangeRecordFetcher,
    SidraIpcaProvider,
    SnapshotDataFrameFetcher,
    SnapshotDateListFetcher,
)

__all__ = [
    "SilverPartitionRef",
    "SilverResult",
    "SilverTransform",
    "AnbimaFeedClient",
    "BronzeExtractor",
    "BronzePartitionRef",
    "BronzeResult",
    "DateRangeDataFrameFetcher",
    "DateRangeRecordFetcher",
    "ExtractResult",
    "SidraIpcaProvider",
    "SnapshotDataFrameFetcher",
    "SnapshotDateListFetcher",
]
