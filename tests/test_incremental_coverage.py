"""Testes de cobertura incremental por conteúdo e watermarks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from rf_lake.incremental import (
    missing_dates_bronze,
    silver_paths_for_dataset,
)
from rf_lake.watermarks import (
    WATERMARKS_PATH,
    get_watermark,
    rebuild_watermarks_from_disk,
    set_watermark,
)


def _write_ms_parquet(path: Path, dates: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in dates:
        rows.append(
            {
                "data_referencia": d,
                "tipo_titulo": "LTN",
                "data_vencimento": "2027-01-01",
            }
        )
    pd.DataFrame(rows).to_parquet(path, index=False)


@pytest.fixture
def isolated_bronze_ms(monkeypatch, tmp_path):
    root = tmp_path / "raw"
    dataset_dir = root / "mercado_secundario"
    dataset_dir.mkdir(parents=True)
    monkeypatch.setattr("rf_lake.incremental.BRONZE_ROOT", root)
    return dataset_dir


@pytest.fixture
def isolated_silver_ms(monkeypatch, tmp_path):
    root = tmp_path / "silver"
    dataset_dir = root / "mercado_secundario"
    dataset_dir.mkdir(parents=True)
    monkeypatch.setattr("rf_lake.incremental.SILVER_ROOT", root)
    return dataset_dir


@pytest.fixture
def isolated_watermarks(monkeypatch, tmp_path):
    meta = tmp_path / "meta"
    meta.mkdir()
    path = meta / "dataset_watermarks.json"
    monkeypatch.setattr("rf_lake.watermarks.META_DIR", meta)
    monkeypatch.setattr("rf_lake.watermarks.WATERMARKS_PATH", path)
    return path


def test_missing_bronze_filename_15_but_content_only_14(isolated_bronze_ms):
    _write_ms_parquet(
        isolated_bronze_ms / "2026-01-01__2026-05-15.parquet",
        ["2026-01-02", "2026-05-14"],
    )
    missing = missing_dates_bronze(
        "mercado_secundario",
        ["2026-05-15"],
    )
    assert missing == ["2026-05-15"]


def test_empty_parquet_does_not_cover_date(isolated_bronze_ms):
    path = isolated_bronze_ms / "2026-05-15__2026-05-15.parquet"
    pd.DataFrame(columns=["data_referencia"]).to_parquet(path, index=False)
    assert path.stat().st_size > 0
    missing = missing_dates_bronze("mercado_secundario", ["2026-05-15"])
    assert missing == ["2026-05-15"]


def test_silver_paths_only_selects_files_with_needed_date(isolated_silver_ms):
    _write_ms_parquet(
        isolated_silver_ms / "2026-01-01__2026-05-14.parquet",
        ["2026-05-14"],
    )
    paths = silver_paths_for_dataset("mercado_secundario", ["2026-05-15"])
    assert paths == []


def test_watermark_not_updated_on_empty_dates(isolated_watermarks):
    set_watermark("mercado_secundario", "bronze", [])
    assert not WATERMARKS_PATH.exists() or get_watermark("mercado_secundario", "bronze") is None

    set_watermark("mercado_secundario", "bronze", ["2026-05-14"])
    assert get_watermark("mercado_secundario", "bronze") == "2026-05-14"

    set_watermark("mercado_secundario", "bronze", ["2026-05-15"])
    assert get_watermark("mercado_secundario", "bronze") == "2026-05-15"


def test_leiloes_bronze_dates_from_dd_mm_yyyy():
    import pandas as pd

    from rf_lake.date_fields import dates_present_in_dataframe

    df = pd.DataFrame({"data_leilao": ["14/01/2026", "15/01/2026"]})
    assert dates_present_in_dataframe(df, "leiloes", layer="bronze") == [
        "2026-01-14",
        "2026-01-15",
    ]


def test_rebuild_watermarks_from_disk(isolated_bronze_ms, isolated_watermarks, monkeypatch):
    monkeypatch.setattr("rf_lake.watermarks.BRONZE_ROOT", isolated_bronze_ms.parent)
    _write_ms_parquet(
        isolated_bronze_ms / "2026-01-01__2026-05-15.parquet",
        ["2026-05-10", "2026-05-14"],
    )
    summary = rebuild_watermarks_from_disk()
    assert summary["mercado_secundario"]["bronze"] == "2026-05-14"
