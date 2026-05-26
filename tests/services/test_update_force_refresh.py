"""E2E force refresh: update(force=True) + read_data() across BMF, CDI, and IPCA."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from app.core.dates import calendar_days
from app.database import MIGRATIONS_DIR, apply_migrations
from app.database.connection import get_connection
from app.database.schema import IPCA_DICT_COLUMNS
from app.lake.bronze.writer import write_partition_parquet as write_bronze_parquet
from app.lake.silver.writer import write_partition_parquet as write_silver_parquet
from app.public import read_data, update
from app.repositories.bmf import BmfRepository
from app.repositories.cdi import CdiRepository
from app.repositories.feriados import FeriadosRepository
from app.repositories.ipca_dict import IpcaDictRepository
from app.services.local_environment_service import ensure_local_environment

_REF_DATE = "2026-05-25"
_WRONG_CDI = 0.01
_CORRECT_CDI = 0.1375

_BMF_BRONZE_ROW = {
    "RptDt": _REF_DATE,
    "TckrSymb": "DI1F27",
    "ISIN": "BR0000000001",
    "XprtnDt": "2027-01-01",
    "AdjstdQtTax": "13,5",
    "AdjstdQt": "100",
}

_BMF_SILVER_ROW = {
    "data_referencia": _REF_DATE,
    "ticker": "DI1F27",
    "codigo_isin": "BR0000000001",
    "data_vencimento": "2027-01-01",
    "taxa_ajuste": 13.5,
    "quantidade_ajuste": 100.0,
}

_IPCA_SILVER_MONTHS = (
    "2025-09-01",
    "2025-10-01",
    "2025-11-01",
    "2025-12-01",
    "2026-01-01",
    "2026-02-01",
    "2026-03-01",
    "2026-04-01",
    "2026-05-01",
)

_PROJ_SILVER = pd.DataFrame(
    [
        {
            "indice": "IPCA",
            "tipo_projecao": "PROJEÇÕES PARA O MÊS CORRENTE",
            "ref_month": "2026-05-01",
            "data_coleta": "2026-05-05",
            "data_validade": pd.NA,
            "variacao_projetada": 0.45,
        }
    ]
)


@pytest.fixture(autouse=True)
def _data_start_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_START_DATE", "2026-01-01")
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _pkg_root(tmp_path: Path) -> Path:
    return tmp_path / "pkg"


def _setup_env(tmp_path: Path) -> Path:
    root = _pkg_root(tmp_path)
    env = ensure_local_environment(data_root=root, create=True)
    apply_migrations(db_path=env.sqlite_db_path, migrations_dir=MIGRATIONS_DIR)
    return root


def _sql_ipca_dates(db: Path) -> list[str]:
    conn = get_connection(db)
    try:
        cur = conn.execute(
            "SELECT data_referencia FROM IPCA_DICT ORDER BY data_referencia"
        )
        return [str(row[0])[:10] for row in cur.fetchall()]
    finally:
        conn.close()


def _seed_bmf_di1_only(env_root: Path, db: Path) -> None:
    env = ensure_local_environment(data_root=env_root, create=False)
    from app.config import get_settings

    settings = get_settings()
    settings.activate_path_overlay(env)
    try:
        write_bronze_parquet(
            "ajustes_bmf",
            "data",
            _REF_DATE,
            pd.DataFrame([_BMF_BRONZE_ROW]),
            "parquet",
        )
        write_silver_parquet(
            "ajustes_bmf",
            "data",
            _REF_DATE,
            pd.DataFrame([_BMF_SILVER_ROW]),
        )
        BmfRepository().upsert(pd.DataFrame([_BMF_SILVER_ROW]), db_path=db)
    finally:
        settings.deactivate_path_overlay()


def _bmf_mock_with_dap(_dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            _BMF_BRONZE_ROW,
            {
                "RptDt": _REF_DATE,
                "TckrSymb": "DAPQ26",
                "ISIN": "BR0000000002",
                "XprtnDt": "2026-06-01",
                "AdjstdQtTax": "12,0",
                "AdjstdQt": "50",
            },
        ]
    )


@patch("app.lake.bronze.extractors.ajustes_bmf.scrap_ajustes_bmf_for_dates", side_effect=_bmf_mock_with_dap)
def test_update_force_bmf_refresh_includes_dap(
    _mock_scrap: object,
    tmp_path: Path,
) -> None:
    root = _setup_env(tmp_path)
    db = root / "database" / "app.db"
    _seed_bmf_di1_only(root, db)

    result = update(
        data_root=str(root),
        datasets=["ajustes_bmf"],
        start_date=_REF_DATE,
        end_date=_REF_DATE,
        refresh_dates=[_REF_DATE],
        force=True,
    )

    assert result.invalidation is not None
    assert result.invalidation.gold_rows_deleted >= 1
    assert result.sync_ran is True

    bmf = read_data(data_root=str(root)).ajustes_bmf.fetch_on(_REF_DATE)
    tickers = set(bmf["ticker"].astype(str))
    assert any(t.startswith("DI1") for t in tickers)
    assert any(t.startswith("DAP") for t in tickers)


def _seed_cdi_wrong(env_root: Path, db: Path) -> None:
    env = ensure_local_environment(data_root=env_root, create=False)
    from app.config import get_settings

    settings = get_settings()
    settings.activate_path_overlay(env)
    try:
        bronze = pd.DataFrame(
            [
                {
                    "data_referencia": pd.Timestamp(_REF_DATE),
                    "estimativa_taxa_selic": _WRONG_CDI,
                }
            ]
        )
        write_bronze_parquet("cdi", "data", _REF_DATE, bronze, "parquet")
        silver = pd.DataFrame([{"data_referencia": _REF_DATE, "cdi": _WRONG_CDI}])
        write_silver_parquet("cdi", "data", _REF_DATE, silver)
        CdiRepository().upsert(silver, db_path=db)
    finally:
        settings.deactivate_path_overlay()


def _cdi_mock(day: str) -> pd.DataFrame:
    return pd.DataFrame(
        [{"data_referencia": pd.Timestamp(day), "estimativa_taxa_selic": _CORRECT_CDI}]
    )


@patch("app.lake.bronze.extractors.cdi.fetch_estimativa_selic", side_effect=_cdi_mock)
def test_update_force_cdi_refresh_replaces_gold_value(
    _mock_fetch: object,
    tmp_path: Path,
) -> None:
    root = _setup_env(tmp_path)
    db = root / "database" / "app.db"
    _seed_cdi_wrong(root, db)

    update(
        data_root=str(root),
        datasets=["cdi"],
        start_date=_REF_DATE,
        end_date=_REF_DATE,
        refresh_dates=[_REF_DATE],
        force=True,
    )

    row = read_data(data_root=str(root)).cdi.fetch_on(_REF_DATE)
    assert len(row) == 1
    assert float(row.iloc[0]["cdi"]) == pytest.approx(_CORRECT_CDI)


def _ipca_silver_month_df(month: str, index: float) -> pd.DataFrame:
    return pd.DataFrame(
        [{"ref_month": month, "ipca_index": index, "ipca_mom": 0.5}]
    )


def _seed_ipca_stale_state(env_root: Path, db: Path) -> None:
    env = ensure_local_environment(data_root=env_root, create=False)
    from app.config import get_settings

    settings = get_settings()
    settings.activate_path_overlay(env)
    try:
        for i, month in enumerate(_IPCA_SILVER_MONTHS):
            write_silver_parquet(
                "ipca_indice",
                "reference_month",
                month,
                _ipca_silver_month_df(month, 100.0 + i),
            )
        write_silver_parquet(
            "projecoes",
            "reference_month",
            "2026-05-01",
            _PROJ_SILVER,
        )
    finally:
        settings.deactivate_path_overlay()

    # Gold state (SQLite) can be seeded without overlay; update() sẽ invalidar e rematerializar.
    FeriadosRepository().replace_all(["2026-05-01"], db_path=db)

    stale_days = ("2026-05-01", "2026-05-20", "2026-05-26")
    rows = []
    for day in stale_days:
        row = {c: None for c in IPCA_DICT_COLUMNS}
        row["data_referencia"] = day
        row["usa_fechado"] = 0
        rows.append(row)
    IpcaDictRepository().upsert(pd.DataFrame(rows), db_path=db)


def _sidra_ipca_table_for_may() -> pd.DataFrame:
  rows = []
  for var, code in (("2266", 102.0), ("63", 0.5)):
      rows.append({"D2C": "202605", "D3C": var, "V": code})
  return pd.DataFrame(rows)


@patch(
    "app.lake.bronze.extractors.ipca_indice.SidraIpcaClient.fetch_table_ipca",
    return_value=_sidra_ipca_table_for_may(),
)
def test_update_force_ipca_rebuilds_daily_series_through_end_date(
    _mock_sidra: object,
    tmp_path: Path,
) -> None:
    root = _setup_env(tmp_path)
    db = root / "database" / "app.db"
    _seed_ipca_stale_state(root, db)

    start = "2026-05-20"
    end = "2026-05-22"

    result = update(
        data_root=str(root),
        datasets=["ipca_indice"],
        start_date=start,
        end_date=end,
        refresh_dates=[start],
        force=True,
    )

    assert result.invalidation is not None
    assert result.sync_ran is True

    expected = calendar_days("2026-05-01", end)
    sql_dates = _sql_ipca_dates(db)
    assert sql_dates[: len(expected)] == expected
    assert sql_dates[-1] == "2026-05-26"
    assert len(read_data(data_root=str(root)).ipca_dict.fetch_range("2026-05-01", end)) == len(
        expected
    )
