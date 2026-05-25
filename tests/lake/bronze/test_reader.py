from __future__ import annotations

import pandas as pd
import pytest

from app.core.dates import business_days, months_in_range
from app.lake.bronze.incremental import list_existing_partition_values
from app.core.partitioning import SNAPSHOT_VALUE
from app.lake.bronze.reader import (
    iter_partitions_in_range,
    partition_values_for_range,
    read_partition,
    read_range,
)
from app.lake.bronze.writer import (
    write_partition_json,
    write_partition_parquet,
)


def test_partition_values_for_range_day() -> None:
    values = partition_values_for_range(
        "mercado_secundario", "2026-01-10", "2026-01-12"
    )
    assert values == business_days("2026-01-10", "2026-01-12")


def test_partition_values_for_range_month() -> None:
    values = partition_values_for_range("projecoes", "2026-01-15", "2026-03-02")
    assert values == months_in_range("2026-01-15", "2026-03-02")


def test_partition_values_for_range_snapshot() -> None:
    values = partition_values_for_range("feriados", "2020-01-01", "2030-12-31")
    assert values == [SNAPSHOT_VALUE]


def test_read_range_parquet_roundtrip(bronze_tmp_root) -> None:
    df = pd.DataFrame(
        {
            "DATA MOV": ["15/01/2026", "16/01/2026"],
            "TICKER": ["A", "B"],
        }
    )
    write_partition_parquet("liquidacoes_mercado", "data", "2026-01-15", df.iloc[:1])
    write_partition_parquet("liquidacoes_mercado", "data", "2026-01-16", df.iloc[1:])

    loaded = read_range("liquidacoes_mercado", "2026-01-15", "2026-01-16")
    assert len(loaded) == 2
    assert list(loaded.columns) == ["DATA MOV", "TICKER"]


def test_read_range_json_roundtrip(bronze_tmp_root) -> None:
    write_partition_json(
        "mercado_secundario",
        "data",
        "2026-01-20",
        [{"codigo": "NTNB", "pu": 1000.0}],
    )
    loaded = read_range("mercado_secundario", "2026-01-20", "2026-01-20")
    assert len(loaded) == 1
    assert loaded.iloc[0]["codigo"] == "NTNB"


def test_read_range_monthly(bronze_tmp_root) -> None:
    write_partition_json(
        "projecoes",
        "reference_month",
        "2026-01-01",
        [{"indice": "IPCA", "variacao": 0.5}],
    )
    write_partition_json(
        "projecoes",
        "reference_month",
        "2026-02-01",
        [{"indice": "IPCA", "variacao": 0.4}],
    )
    loaded = read_range("projecoes", "2026-01-01", "2026-02-28")
    assert len(loaded) == 2


def test_read_range_snapshot_feriados(bronze_tmp_root) -> None:
    write_partition_parquet(
        "feriados",
        "snapshot",
        SNAPSHOT_VALUE,
        pd.DataFrame({"Data": ["2026-01-01", "2026-01-02"]}),
    )
    loaded = read_range("feriados", "2020-01-01", "2030-12-31")
    assert len(loaded) == 2


def test_read_range_skip_missing(bronze_tmp_root) -> None:
    write_partition_json("mercado_secundario", "data", "2026-01-20", [{"x": 1}])
    loaded = read_range(
        "mercado_secundario",
        "2026-01-20",
        "2026-01-22",
        only_existing=False,
    )
    assert len(loaded) == 1


def test_read_range_skip_missing_false_raises(bronze_tmp_root) -> None:
    write_partition_json("mercado_secundario", "data", "2026-01-20", [{"x": 1}])
    with pytest.raises(FileNotFoundError):
        read_range(
            "mercado_secundario",
            "2026-01-20",
            "2026-01-22",
            skip_missing=False,
            only_existing=False,
        )


def test_add_partition_column(bronze_tmp_root) -> None:
    write_partition_json("mercado_secundario", "data", "2026-01-20", [{"x": 1}])
    loaded = read_partition(
        "mercado_secundario", "2026-01-20", add_partition_column=True
    )
    assert "_partition_data" in loaded.columns
    assert loaded.iloc[0]["_partition_data"] == "2026-01-20"


def test_iter_partitions_in_range(bronze_tmp_root) -> None:
    write_partition_json("mercado_secundario", "data", "2026-01-20", [{"x": 1}])
    refs = list(
        iter_partitions_in_range("mercado_secundario", "2026-01-20", "2026-01-22")
    )
    assert len(refs) == 1
    assert refs[0].partition_value == "2026-01-20"
    assert refs[0].path.is_file()


def test_list_existing_partition_values_reexport(bronze_tmp_root) -> None:
    write_partition_json("mercado_secundario", "data", "2026-01-20", [{"x": 1}])
    values = list_existing_partition_values("mercado_secundario")
    assert values == ["2026-01-20"]
