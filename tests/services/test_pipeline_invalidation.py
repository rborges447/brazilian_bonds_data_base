from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.core.datasets import DATASETS
from app.database.connection import get_connection
from app.core.partitioning import SNAPSHOT_VALUE
from app.database import MIGRATIONS_DIR, apply_migrations
from app.lake.bronze.paths import bronze_partition_path
from app.lake.gold.contracts import BUILDER_NAMES
from app.lake.gold.incremental import BUILDER_TABLE
from app.lake.silver.paths import silver_partition_path
from app.repositories.bmf import BmfRepository
from app.repositories.cdi import CdiRepository
from app.repositories.feriados import FeriadosRepository
from app.repositories.ipca_dict import IpcaDictRepository
from app.repositories.vna import VnaRepository
from app.services.pipeline_invalidation import (
    _remove_partition_artifact,
    invalidate_bronze_partitions,
    invalidate_gold_persisted,
    invalidate_silver_partitions,
    resolve_invalidation_scope,
)


def _touch_bronze(_lake_root: Path, dataset: str, partition_key: str, value: str, ext: str) -> Path:
    path = bronze_partition_path(dataset, partition_key, value, ext)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"test")
    return path


def _touch_silver(_lake_root: Path, dataset: str, partition_key: str, value: str) -> Path:
    path = silver_partition_path(dataset, partition_key, value, "parquet")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"test")
    return path


def _migrate(db: Path) -> None:
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)


def _sql_dates(db: Path, table: str, col: str) -> list[str]:
    conn = get_connection(db)
    try:
        cur = conn.execute(f"SELECT {col} FROM {table} ORDER BY {col}")
        return [str(row[0])[:10] for row in cur.fetchall()]
    finally:
        conn.close()


def test_resolve_all_datasets_when_none() -> None:
    scope = resolve_invalidation_scope(
        datasets=None,
        start_date="2026-05-25",
        end_date="2026-05-25",
    )
    assert set(scope.datasets) == set(DATASETS.keys())
    assert len(scope.datasets) == 10
    assert "vna" in scope.builders
    assert len(scope.builders) == len(BUILDER_NAMES)


def test_resolve_refresh_dates_restricts_daily() -> None:
    scope = resolve_invalidation_scope(
        datasets=["cdi"],
        start_date="2026-01-01",
        end_date="2026-05-31",
        refresh_dates=["2026-05-25"],
    )
    assert scope.partition_values_by_dataset["cdi"] == ("2026-05-25",)
    assert scope.gold_delete_dates_by_builder["cdi"] == ("2026-05-25",)


def test_invalidate_bronze_daily(lake_tmp_root: Path) -> None:
    path = _touch_bronze(lake_tmp_root, "cdi", "data", "2026-05-25", "parquet")
    scope = resolve_invalidation_scope(
        datasets=["cdi"],
        start_date="2026-05-25",
        end_date="2026-05-25",
        refresh_dates=["2026-05-25"],
    )
    removed = invalidate_bronze_partitions(scope)
    assert removed == 1
    assert not path.is_file()


def test_invalidate_bronze_monthly(lake_tmp_root: Path) -> None:
    path = _touch_bronze(
        lake_tmp_root, "projecoes", "reference_month", "2026-05-01", "json"
    )
    scope = resolve_invalidation_scope(
        datasets=["projecoes"],
        start_date="2026-05-01",
        end_date="2026-05-01",
        refresh_dates=["2026-05-15"],
    )
    removed = invalidate_bronze_partitions(scope)
    assert removed == 1
    assert not path.is_file()


def test_invalidate_bronze_snapshot(lake_tmp_root: Path) -> None:
    path = _touch_bronze(lake_tmp_root, "feriados", "snapshot", SNAPSHOT_VALUE, "parquet")
    scope = resolve_invalidation_scope(
        datasets=["feriados"],
        start_date="2026-05-25",
        end_date="2026-05-25",
    )
    removed = invalidate_bronze_partitions(scope)
    assert removed == 1
    assert not path.is_file()


def test_invalidate_silver_daily(lake_tmp_root: Path) -> None:
    path = _touch_silver(lake_tmp_root, "cdi", "data", "2026-05-25")
    scope = resolve_invalidation_scope(
        datasets=["cdi"],
        start_date="2026-05-25",
        end_date="2026-05-25",
        refresh_dates=["2026-05-25"],
    )
    removed = invalidate_silver_partitions(scope)
    assert removed == 1
    assert not path.is_file()


def test_invalidate_silver_monthly(lake_tmp_root: Path) -> None:
    path = _touch_silver(lake_tmp_root, "ipca_indice", "reference_month", "2026-05-01")
    scope = resolve_invalidation_scope(
        datasets=["ipca_indice"],
        start_date="2026-05-01",
        end_date="2026-05-01",
        refresh_dates=["2026-05-20"],
    )
    removed = invalidate_silver_partitions(scope)
    assert removed == 1
    assert not path.is_file()


def test_invalidate_silver_snapshot(lake_tmp_root: Path) -> None:
    path = _touch_silver(lake_tmp_root, "feriados", "snapshot", SNAPSHOT_VALUE)
    scope = resolve_invalidation_scope(
        datasets=["feriados"],
        start_date="2026-05-25",
        end_date="2026-05-25",
    )
    removed = invalidate_silver_partitions(scope)
    assert removed == 1
    assert not path.is_file()


def test_invalidate_gold_daily(lake_tmp_root: Path) -> None:
    db = lake_tmp_root / "test.db"
    _migrate(db)
    CdiRepository().upsert(
        pd.DataFrame(
            [
                {"data_referencia": "2026-05-24", "cdi": 0.01},
                {"data_referencia": "2026-05-25", "cdi": 0.02},
            ]
        ),
        db_path=db,
    )
    scope = resolve_invalidation_scope(
        datasets=["cdi"],
        start_date="2026-05-25",
        end_date="2026-05-25",
        refresh_dates=["2026-05-25"],
    )
    deleted = invalidate_gold_persisted(scope, db)
    assert deleted == 1
    assert _sql_dates(db, "CDI", "data_referencia") == ["2026-05-24"]


def test_invalidate_gold_feriados(lake_tmp_root: Path) -> None:
    db = lake_tmp_root / "test.db"
    _migrate(db)
    FeriadosRepository().replace_all(["2026-01-01", "2026-05-01"], db_path=db)
    scope = resolve_invalidation_scope(
        datasets=["feriados"],
        start_date="2026-05-25",
        end_date="2026-05-25",
    )
    deleted = invalidate_gold_persisted(scope, db)
    assert deleted == 2
    assert FeriadosRepository().list_dates(db_path=db) == []


def test_resolve_feriados_snapshot_partition_value() -> None:
    scope = resolve_invalidation_scope(
        datasets=["feriados"],
        start_date="2026-05-25",
        end_date="2026-05-31",
        refresh_dates=["2026-05-25"],
    )
    assert scope.partition_values_by_dataset["feriados"] == (SNAPSHOT_VALUE,)
    assert scope.builders == ("feriados",)
    assert scope.ipca_dict_calendar_days == ()

    scope_no_refresh = resolve_invalidation_scope(
        datasets=["feriados"],
        start_date="2026-01-01",
        end_date="2026-12-31",
        refresh_dates=None,
    )
    assert scope_no_refresh.partition_values_by_dataset["feriados"] == (SNAPSHOT_VALUE,)


def _seed_feriados_cdi_lake_and_gold(lake_root: Path, db: Path) -> dict[str, Path]:
    _migrate(db)
    paths = {
        "feriados_bronze": _touch_bronze(
            lake_root, "feriados", "snapshot", SNAPSHOT_VALUE, "parquet"
        ),
        "feriados_silver": _touch_silver(lake_root, "feriados", "snapshot", SNAPSHOT_VALUE),
        "cdi_bronze": _touch_bronze(lake_root, "cdi", "data", _REF_DATE, "parquet"),
        "cdi_silver": _touch_silver(lake_root, "cdi", "data", _REF_DATE),
    }
    FeriadosRepository().replace_all(["2026-01-01", "2026-05-01"], db_path=db)
    CdiRepository().upsert(
        pd.DataFrame([{"data_referencia": _REF_DATE, "cdi": 0.01}]),
        db_path=db,
    )
    return paths


def test_invalidate_feriados_scope_does_not_touch_cdi(lake_tmp_root: Path) -> None:
    db = lake_tmp_root / "test.db"
    paths = _seed_feriados_cdi_lake_and_gold(lake_tmp_root, db)
    scope = resolve_invalidation_scope(
        datasets=["feriados"],
        start_date=_REF_DATE,
        end_date=_REF_DATE,
    )

    assert "cdi" not in scope.partition_values_by_dataset
    assert scope.builders == ("feriados",)

    invalidate_bronze_partitions(scope)
    invalidate_silver_partitions(scope)
    invalidate_gold_persisted(scope, db)

    assert not paths["feriados_bronze"].is_file()
    assert not paths["feriados_silver"].is_file()
    assert paths["cdi_bronze"].is_file()
    assert paths["cdi_silver"].is_file()
    assert FeriadosRepository().list_dates(db_path=db) == []
    assert _sql_dates(db, "CDI", "data_referencia") == [_REF_DATE]


def test_invalidate_feriados_full_pipeline_layers(lake_tmp_root: Path) -> None:
    db = lake_tmp_root / "test.db"
    _touch_bronze(lake_tmp_root, "feriados", "snapshot", SNAPSHOT_VALUE, "parquet")
    _touch_silver(lake_tmp_root, "feriados", "snapshot", SNAPSHOT_VALUE)
    _migrate(db)
    FeriadosRepository().replace_all(["2026-01-01", "2026-05-01"], db_path=db)

    scope = resolve_invalidation_scope(
        datasets=["feriados"],
        start_date="2026-05-25",
        end_date="2026-05-25",
    )
    bronze_removed = invalidate_bronze_partitions(scope)
    silver_removed = invalidate_silver_partitions(scope)
    gold_deleted = invalidate_gold_persisted(scope, db)

    assert bronze_removed == 1
    assert silver_removed == 1
    assert gold_deleted == 2
    assert FeriadosRepository().list_dates(db_path=db) == []
    assert not (
        lake_tmp_root / "raw" / "feriados" / f"snapshot={SNAPSHOT_VALUE}" / "part.parquet"
    ).is_file()
    assert not (
        lake_tmp_root
        / "silver"
        / "feriados"
        / f"snapshot={SNAPSHOT_VALUE}"
        / "part.parquet"
    ).is_file()


def test_invalidate_gold_ipca_dict(lake_tmp_root: Path) -> None:
    from app.database.schema import IPCA_DICT_COLUMNS

    db = lake_tmp_root / "test.db"
    _migrate(db)
    rows = []
    for day in ("2026-05-24", "2026-05-25", "2026-05-26"):
        row = {c: None for c in IPCA_DICT_COLUMNS}
        row["data_referencia"] = day
        row["usa_fechado"] = 0
        rows.append(row)
    IpcaDictRepository().upsert(pd.DataFrame(rows), db_path=db)

    scope = resolve_invalidation_scope(
        datasets=["ipca_indice"],
        start_date="2026-05-24",
        end_date="2026-05-26",
        refresh_dates=["2026-05-24"],
    )
    assert scope.ipca_dict_calendar_days[0] == "2026-05-01"
    assert scope.ipca_dict_calendar_days[-1] == "2026-05-26"
    assert len(scope.ipca_dict_calendar_days) == 26
    deleted = invalidate_gold_persisted(scope, db)
    assert deleted == 3

    assert _sql_dates(db, "IPCA_DICT", "data_referencia") == []


def test_ipca_refresh_invalidates_month_partition() -> None:
    scope = resolve_invalidation_scope(
        datasets=["ipca_indice"],
        start_date="2026-05-24",
        end_date="2026-05-26",
        refresh_dates=["2026-05-24"],
    )
    assert scope.partition_values_by_dataset["ipca_indice"] == ("2026-05-01",)


def test_ipca_dict_rebuild_from_month_start_not_refresh_day() -> None:
    scope = resolve_invalidation_scope(
        datasets=["ipca_indice"],
        start_date="2026-05-24",
        end_date="2026-05-26",
        refresh_dates=["2026-05-24"],
    )
    assert min(scope.ipca_dict_calendar_days) == "2026-05-01"
    assert min(scope.ipca_dict_calendar_days) != "2026-05-24"


def test_ipca_only_projecoes_in_scope_invalidates_proj_month_only() -> None:
    scope = resolve_invalidation_scope(
        datasets=["projecoes"],
        start_date="2026-05-20",
        end_date="2026-05-20",
        refresh_dates=["2026-05-20"],
    )
    assert set(scope.partition_values_by_dataset.keys()) == {"projecoes"}
    assert scope.partition_values_by_dataset["projecoes"] == ("2026-05-01",)
    assert "ipca_indice" not in scope.partition_values_by_dataset


def test_ipca_wide_window_without_refresh_uses_sync_ipca_months(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-05-01")
    from app.config import get_settings

    get_settings.cache_clear()
    scope = resolve_invalidation_scope(
        datasets=["ipca_indice"],
        start_date="2026-05-01",
        end_date="2026-05-31",
        refresh_dates=None,
    )
    months = scope.partition_values_by_dataset["ipca_indice"]
    assert "2026-05-01" in months
    assert scope.ipca_dict_calendar_days[0] == min(months)
    assert scope.ipca_dict_calendar_days[-1] == "2026-05-31"
    assert len(scope.ipca_dict_calendar_days) > len(months)


def test_path_safety_rejects_outside_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside" / "part.parquet"
    outside.parent.mkdir(parents=True)
    outside.write_bytes(b"x")
    lake_root = tmp_path / "raw"
    lake_root.mkdir()
    with pytest.raises(ValueError, match="outside lake root"):
        _remove_partition_artifact(outside, lake_root)


def test_invalidate_bronze_missing_partition_is_noop(lake_tmp_root: Path) -> None:
    scope = resolve_invalidation_scope(
        datasets=["cdi"],
        start_date="2026-05-25",
        end_date="2026-05-25",
        refresh_dates=["2026-05-25"],
    )
    assert invalidate_bronze_partitions(scope) == 0


def test_unknown_dataset_raises() -> None:
    with pytest.raises(ValueError, match="Unknown dataset"):
        resolve_invalidation_scope(
            datasets=["not_a_dataset"],
            start_date="2026-05-25",
            end_date="2026-05-25",
        )


_REF_DATE = "2026-05-25"
_SCOPE_KW = {
    "start_date": _REF_DATE,
    "end_date": _REF_DATE,
    "refresh_dates": [_REF_DATE],
}


def _seed_cdi_bmf_lake_and_gold(lake_root: Path, db: Path) -> dict[str, Path]:
    """Seed bronze/silver/gold for cdi and ajustes_bmf on the same reference date."""
    _migrate(db)
    paths = {
        "cdi_bronze": _touch_bronze(lake_root, "cdi", "data", _REF_DATE, "parquet"),
        "cdi_silver": _touch_silver(lake_root, "cdi", "data", _REF_DATE),
        "bmf_bronze": _touch_bronze(
            lake_root, "ajustes_bmf", "data", _REF_DATE, "parquet"
        ),
        "bmf_silver": _touch_silver(lake_root, "ajustes_bmf", "data", _REF_DATE),
    }
    CdiRepository().upsert(
        pd.DataFrame([{"data_referencia": _REF_DATE, "cdi": 0.01}]),
        db_path=db,
    )
    BmfRepository().upsert(
        pd.DataFrame(
            [
                {
                    "ticker": "DI1F27",
                    "codigo_isin": None,
                    "data_vencimento": "2027-01-01",
                    "data_referencia": _REF_DATE,
                    "taxa_ajuste": 0.0,
                    "quantidade_ajuste": 1.0,
                }
            ]
        ),
        db_path=db,
    )
    return paths


def test_invalidate_cdi_scope_does_not_touch_ajustes_bmf(lake_tmp_root: Path) -> None:
    db = lake_tmp_root / "test.db"
    paths = _seed_cdi_bmf_lake_and_gold(lake_tmp_root, db)
    scope = resolve_invalidation_scope(datasets=["cdi"], **_SCOPE_KW)

    assert "ajustes_bmf" not in scope.partition_values_by_dataset
    assert scope.builders == ("cdi",)

    invalidate_bronze_partitions(scope)
    invalidate_silver_partitions(scope)
    invalidate_gold_persisted(scope, db)

    assert not paths["cdi_bronze"].is_file()
    assert not paths["cdi_silver"].is_file()
    assert paths["bmf_bronze"].is_file()
    assert paths["bmf_silver"].is_file()
    assert _sql_dates(db, "CDI", "data_referencia") == []
    assert _sql_dates(db, "AJUSTES_BMF", "data_referencia") == [_REF_DATE]


def test_invalidate_ajustes_bmf_scope_does_not_touch_cdi(lake_tmp_root: Path) -> None:
    db = lake_tmp_root / "test.db"
    paths = _seed_cdi_bmf_lake_and_gold(lake_tmp_root, db)
    scope = resolve_invalidation_scope(datasets=["ajustes_bmf"], **_SCOPE_KW)

    assert "cdi" not in scope.partition_values_by_dataset
    assert scope.builders == ("bmf",)

    invalidate_bronze_partitions(scope)
    invalidate_silver_partitions(scope)
    invalidate_gold_persisted(scope, db)

    assert paths["cdi_bronze"].is_file()
    assert paths["cdi_silver"].is_file()
    assert not paths["bmf_bronze"].is_file()
    assert not paths["bmf_silver"].is_file()
    assert _sql_dates(db, "CDI", "data_referencia") == [_REF_DATE]
    assert _sql_dates(db, "AJUSTES_BMF", "data_referencia") == []


@pytest.mark.parametrize(
    ("dataset", "expected_builder"),
    [
        ("cdi", "cdi"),
        ("ptax", "ptax"),
        ("mercado_secundario", "mercado_secundario"),
        ("liquidacoes_mercado", "liquidacoes_mercado"),
        ("leiloes", "leiloes"),
        ("ajustes_bmf", "bmf"),
        ("ipca_indice", "ipca_dict"),
        ("projecoes", "ipca_dict"),
        ("feriados", "feriados"),
        ("vna", "vna"),
    ],
)
def test_resolve_maps_dataset_to_builder(dataset: str, expected_builder: str) -> None:
    scope = resolve_invalidation_scope(
        datasets=[dataset],
        start_date=_REF_DATE,
        end_date=_REF_DATE,
        refresh_dates=[_REF_DATE] if dataset not in ("feriados",) else None,
    )
    assert scope.builders == (expected_builder,)
    assert expected_builder in BUILDER_TABLE
    table, date_col = BUILDER_TABLE[expected_builder]  # type: ignore[literal-required]
    assert table
    assert date_col


def _vna_row(**overrides: object) -> dict:
    row = {
        "data_referencia": "2026-05-25",
        "codigo_selic": 210100,
        "tipo_correcao": "O",
        "index": 14.65,
        "data_validade": "2025-05-23",
        "vna": 16616.59,
        "vna_ajustado": None,
    }
    row.update(overrides)
    return row


def test_invalidate_gold_vna(lake_tmp_root: Path) -> None:
    db = lake_tmp_root / "test.db"
    _migrate(db)
    VnaRepository().upsert(
        pd.DataFrame(
            [
                _vna_row(data_referencia="2026-05-24", codigo_selic=210100),
                _vna_row(data_referencia="2026-05-24", codigo_selic=210200),
                _vna_row(data_referencia="2026-05-25", codigo_selic=210100),
            ]
        ),
        db_path=db,
    )
    scope = resolve_invalidation_scope(
        datasets=["vna"],
        start_date="2026-05-25",
        end_date="2026-05-25",
        refresh_dates=["2026-05-25"],
    )
    deleted = invalidate_gold_persisted(scope, db)
    assert deleted == 1
    assert _sql_dates(db, "VNA", "data_referencia") == ["2026-05-24", "2026-05-24"]


def _seed_vna_cdi_lake_and_gold(lake_root: Path, db: Path) -> dict[str, Path]:
    _migrate(db)
    paths = {
        "vna_bronze": _touch_bronze(lake_root, "vna", "data", _REF_DATE, "json"),
        "vna_silver": _touch_silver(lake_root, "vna", "data", _REF_DATE),
        "cdi_bronze": _touch_bronze(lake_root, "cdi", "data", _REF_DATE, "parquet"),
        "cdi_silver": _touch_silver(lake_root, "cdi", "data", _REF_DATE),
    }
    VnaRepository().upsert(
        pd.DataFrame([_vna_row()]),
        db_path=db,
    )
    CdiRepository().upsert(
        pd.DataFrame([{"data_referencia": _REF_DATE, "cdi": 0.01}]),
        db_path=db,
    )
    return paths


def test_invalidate_vna_scope_does_not_touch_cdi(lake_tmp_root: Path) -> None:
    db = lake_tmp_root / "test.db"
    paths = _seed_vna_cdi_lake_and_gold(lake_tmp_root, db)
    scope = resolve_invalidation_scope(datasets=["vna"], **_SCOPE_KW)

    assert "cdi" not in scope.partition_values_by_dataset
    assert scope.builders == ("vna",)

    invalidate_bronze_partitions(scope)
    invalidate_silver_partitions(scope)
    invalidate_gold_persisted(scope, db)

    assert not paths["vna_bronze"].is_file()
    assert not paths["vna_silver"].is_file()
    assert paths["cdi_bronze"].is_file()
    assert paths["cdi_silver"].is_file()
    assert _sql_dates(db, "CDI", "data_referencia") == [_REF_DATE]
    assert _sql_dates(db, "VNA", "data_referencia") == []
