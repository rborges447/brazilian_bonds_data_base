from __future__ import annotations

from pathlib import Path

from app.contracts import BronzePartitionRef, BronzeResult, ExtractResult
from app.core.partitioning import PARTITION_SPECS, PIPELINE_NAMES, get_partition_spec
from app.lake.bronze.registry import EXTRACTORS
from app.core.datasets import DATASETS

def test_extract_result_dataclass() -> None:
    result = ExtractResult(
        path=Path("data/raw/x.parquet"),
        row_count=10,
        segment_keys=["2026-01-01"],
    )
    assert result.path == Path("data/raw/x.parquet")
    assert result.row_count == 10
    assert result.segment_keys == ["2026-01-01"]

    empty = ExtractResult(path=None, row_count=0, segment_keys=[])
    assert empty.path is None


def test_bronze_partition_ref() -> None:
    ref = BronzePartitionRef(
        dataset="mercado_secundario",
        partition_key="data",
        partition_value="2026-01-15",
        path=Path("data/raw/mercado_secundario/data=2026-01-15/part.json"),
    )
    assert ref.partition_value == "2026-01-15"


def test_bronze_result_defaults() -> None:
    result = BronzeResult(name="ipca_indice", status="skipped")
    assert result.segment_keys == []
    assert result.dates_candidate == []


def test_pipeline_names_match_partition_specs() -> None:
    assert set(PIPELINE_NAMES) == set(PARTITION_SPECS.keys())


def test_datasets_align_with_partition_specs() -> None:
    assert set(DATASETS) == set(PARTITION_SPECS)


def test_every_pipeline_has_extractor() -> None:
    assert set(EXTRACTORS.keys()) == set(PIPELINE_NAMES)


def test_vna_partition_spec() -> None:
    spec = get_partition_spec("vna")
    assert spec.partition_key == "data"
    assert spec.granularity == "day"
    assert spec.artifact_ext == "json"
