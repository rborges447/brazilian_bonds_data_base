from __future__ import annotations

from models.dates import months_in_range


def test_months_in_range_inclusive() -> None:
    assert months_in_range("2026-01-15", "2026-03-02") == [
        "2026-01-01",
        "2026-02-01",
        "2026-03-01",
    ]


def test_months_in_range_empty_when_start_after_end() -> None:
    assert months_in_range("2026-05-01", "2026-01-01") == []


def test_months_in_range_single_month() -> None:
    assert months_in_range("2026-04-10", "2026-04-20") == ["2026-04-01"]
