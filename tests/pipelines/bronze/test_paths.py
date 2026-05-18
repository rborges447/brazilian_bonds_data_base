from __future__ import annotations

from pipelines.bronze.paths import bronze_partition_path


def test_bronze_partition_path_hive_layout(bronze_tmp_root) -> None:
    path = bronze_partition_path("liquidacoes_mercado", "data", "2026-01-15", "parquet")
    assert path == bronze_tmp_root / "liquidacoes_mercado" / "data=2026-01-15" / "part.parquet"


def test_bronze_partition_path_cdi(bronze_tmp_root) -> None:
    path = bronze_partition_path("cdi", "data", "2026-01-15", "parquet")
    assert path == bronze_tmp_root / "cdi" / "data=2026-01-15" / "part.parquet"
