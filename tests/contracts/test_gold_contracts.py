from __future__ import annotations

from app.lake.gold.contracts import (
    BUILDER_NAMES,
    BUILDER_SILVER_DATASETS,
    PASS_THROUGH_NAMES,
)


def test_vna_gold_contracts() -> None:
    assert "vna" in BUILDER_NAMES
    assert "vna_lft" not in BUILDER_NAMES
    assert "vna" in PASS_THROUGH_NAMES
    assert BUILDER_SILVER_DATASETS["vna"] == ("vna",)
