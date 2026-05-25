from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.database import MIGRATIONS_DIR, apply_migrations
from app.database.readers import GoldReader
from app.repositories.cdi import CdiRepository
from app.repositories.liquidacoes_mercado import LiquidacoesMercadoRepository
from app.repositories.mercado_secundario import MercadoSecundarioRepository


def _migrate(db: Path) -> None:
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)


def _titulo_row(**overrides: object) -> dict:
    base = {
        "tipo_titulo": "LTN",
        "data_vencimento": "2027-01-01",
        "expressao": None,
        "data_base": "2000-01-01",
        "codigo_selic": "100000",
        "codigo_isin": "BRSTNCNTF007",
        "status": "ATIVO",
    }
    base.update(overrides)
    return base


def _mercado_row(data_referencia: str, **overrides: object) -> dict:
    base = {
        "tipo_titulo": "LTN",
        "data_vencimento": "2027-01-01",
        "data_referencia": data_referencia,
        "taxa_anbima": 10.0,
        "intervalo_min_d0": 9.0,
        "intervalo_max_d0": 11.0,
        "intervalo_min_d1": 8.0,
        "intervalo_max_d1": 12.0,
        "pu": 500.0,
        "expressao": None,
        "data_base": "2000-01-01",
        "codigo_selic": "100000",
        "codigo_isin": "BRSTNCNTF007",
        "taxa_compra": None,
        "taxa_venda": None,
        "desvio_padrao": None,
        "status": "ATIVO",
    }
    base.update(overrides)
    return base


def _liq_row(data_referencia: str, **overrides: object) -> dict:
    base = {
        "tipo_titulo": "LTN",
        "data_vencimento": "2027-01-01",
        "data_referencia": data_referencia,
        "qtd_operacoes": 5,
        "qtd_titulos": 100.0,
        "pu_medio": 500.0,
        "expressao": None,
        "data_base": "2000-01-01",
        "codigo_selic": "100000",
        "codigo_isin": "BRSTNCNTF007",
        "status": "ATIVO",
    }
    base.update(overrides)
    return base


def test_cdi_date_series_readers(tmp_path: Path) -> None:
    db = tmp_path / "read.db"
    _migrate(db)
    CdiRepository().upsert(
        pd.DataFrame(
            [
                {"data_referencia": "2026-01-02", "cdi": 0.01},
                {"data_referencia": "2026-01-03", "cdi": 0.02},
                {"data_referencia": "2026-01-05", "cdi": 0.03},
            ]
        ),
        db_path=db,
    )
    reader = GoldReader(db_path=db)
    assert len(reader.cdi.fetch_latest(2)) == 2
    assert reader.cdi.fetch_latest(2).iloc[0]["data_referencia"] == "2026-01-05"
    assert len(reader.cdi.fetch_on("2026-01-03")) == 1
    assert len(reader.cdi.fetch_range("2026-01-02", "2026-01-04")) == 2
    assert len(reader.cdi.fetch_all()) == 3


def test_titulos_publicos_static_reader(tmp_path: Path) -> None:
    db = tmp_path / "read.db"
    _migrate(db)
    MercadoSecundarioRepository().upsert(
        pd.DataFrame([_mercado_row("2026-01-15")]),
        db_path=db,
    )
    reader = GoldReader(db_path=db)
    assert len(reader.titulos_publicos.fetch_all()) >= 1
    with pytest.raises(TypeError, match="fetch_all"):
        reader.titulos_publicos.fetch_latest(1)
    with pytest.raises(TypeError, match="fetch_all"):
        reader.titulos_publicos.fetch_on("2026-01-15")


def test_mercado_liquidacoes_full_outer(tmp_path: Path) -> None:
    db = tmp_path / "read.db"
    _migrate(db)
    MercadoSecundarioRepository().upsert(
        pd.DataFrame(
            [
                _mercado_row("2026-01-10"),
                _mercado_row(
                    "2026-01-12",
                    tipo_titulo="NTN-B",
                    data_vencimento="2035-01-01",
                    codigo_selic="200000",
                    codigo_isin="BRSTNCNTF008",
                ),
            ]
        ),
        db_path=db,
    )
    LiquidacoesMercadoRepository().upsert(
        pd.DataFrame(
            [
                _liq_row("2026-01-10"),
                _liq_row(
                    "2026-01-11",
                    tipo_titulo="LFT",
                    data_vencimento="2028-01-01",
                    codigo_selic="300000",
                    codigo_isin="BRSTNCNTF009",
                ),
            ]
        ),
        db_path=db,
    )
    reader = GoldReader(db_path=db)
    join = reader.mercado_com_liquidacoes.fetch_all()
    assert len(join) == 3
    both = join[
        (join["data_referencia"] == "2026-01-10")
        & (join["tipo_titulo"] == "LTN")
    ].iloc[0]
    assert both["taxa_anbima"] == pytest.approx(10.0)
    assert both["qtd_operacoes"] == 5
    mercado_only = join[join["data_referencia"] == "2026-01-12"].iloc[0]
    assert pd.isna(mercado_only["qtd_operacoes"])
    liq_only = join[join["data_referencia"] == "2026-01-11"].iloc[0]
    assert pd.isna(liq_only["taxa_anbima"])
    assert liq_only["qtd_operacoes"] == 5

    on_day = reader.mercado_liquidacoes.fetch_on("2026-01-10")
    assert len(on_day) == 1
    assert on_day.iloc[0]["pu_medio_liq"] == pytest.approx(500.0)

    latest = reader.mercado_com_liquidacoes.fetch_latest(2)
    assert latest["data_referencia"].nunique() == 2
    assert set(latest["data_referencia"]) == {"2026-01-11", "2026-01-12"}
