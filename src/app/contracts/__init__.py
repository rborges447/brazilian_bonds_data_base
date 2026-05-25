"""Layer contracts (types and protocols only — no I/O)."""

from app.contracts.bronze import (
    BronzeExtractor,
    BronzePartitionRef,
    BronzeResult,
    ExtractResult,
)
from app.contracts.silver import SilverPartitionRef, SilverResult, SilverTransform
from app.contracts.providers import (
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
