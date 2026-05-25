"""fetch_latest(n) must return all rows for the last n distinct reference dates."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.database import MIGRATIONS_DIR, apply_migrations
from app.database.readers import GoldReader
from app.repositories.leiloes import LeiloesRepository
from app.repositories.liquidacoes_mercado import LiquidacoesMercadoRepository
from app.repositories.mercado_secundario import MercadoSecundarioRepository


def _migrate(db: Path) -> None:
    apply_migrations(db_path=db, migrations_dir=MIGRATIONS_DIR)


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


def _leilao_row(data_referencia: str, **overrides: object) -> dict:
    base = {
        "numero_edital": "1",
        "tipo_titulo": "LTN",
        "data_vencimento": "2027-01-01",
        "data_referencia": data_referencia,
        "oferta": 100.0,
        "quantidade_aceita": 50.0,
        "percentual_corte": 1.0,
        "oferta_segunda_volta": None,
        "financeiro_aceito": 1000.0,
        "financeiro_aceito_segunda_volta": None,
        "quantidade_aceita_segunda_volta": None,
        "pu_medio": 500.0,
        "taxa_media": 10.0,
    }
    base.update(overrides)
    return base


def test_mercado_secundario_fetch_latest_distinct_dates(tmp_path: Path) -> None:
    db = tmp_path / "read.db"
    _migrate(db)
    MercadoSecundarioRepository().upsert(
        pd.DataFrame(
            [
                _mercado_row("2026-01-01"),
                _mercado_row("2026-01-01", tipo_titulo="LFT", data_vencimento="2028-01-01"),
                _mercado_row("2026-01-02"),
                _mercado_row("2026-01-02", tipo_titulo="LFT", data_vencimento="2028-01-01"),
                _mercado_row("2026-01-03"),
                _mercado_row("2026-01-03", tipo_titulo="LFT", data_vencimento="2028-01-01"),
            ]
        ),
        db_path=db,
    )
    reader = GoldReader(db_path=db)
    latest = reader.mercado_secundario.fetch_latest(2)
    assert latest["data_referencia"].nunique() == 2
    assert set(latest["data_referencia"]) == {"2026-01-02", "2026-01-03"}
    assert len(latest) == 4


def test_leiloes_fetch_latest_distinct_dates(tmp_path: Path) -> None:
    db = tmp_path / "read.db"
    _migrate(db)
    LeiloesRepository().upsert(
        pd.DataFrame(
            [
                _leilao_row("2026-01-01"),
                _leilao_row("2026-01-01", numero_edital="2"),
                _leilao_row("2026-01-02"),
                _leilao_row("2026-01-03"),
            ]
        ),
        db_path=db,
    )
    reader = GoldReader(db_path=db)
    latest = reader.leiloes.fetch_latest(2)
    assert latest["data_referencia"].nunique() == 2
    assert set(latest["data_referencia"]) == {"2026-01-02", "2026-01-03"}
    assert len(latest) == 2


def test_mercado_com_liquidacoes_fetch_latest_distinct_dates(tmp_path: Path) -> None:
    db = tmp_path / "read.db"
    _migrate(db)
    MercadoSecundarioRepository().upsert(
        pd.DataFrame([_mercado_row("2026-01-10"), _mercado_row("2026-01-12")]),
        db_path=db,
    )
    LiquidacoesMercadoRepository().upsert(
        pd.DataFrame(
            [
                {
                    "tipo_titulo": "LTN",
                    "data_vencimento": "2027-01-01",
                    "data_referencia": "2026-01-10",
                    "qtd_operacoes": 5,
                    "qtd_titulos": 100.0,
                    "pu_medio": 500.0,
                    "expressao": None,
                    "data_base": "2000-01-01",
                    "codigo_selic": "100000",
                    "codigo_isin": "BRSTNCNTF007",
                    "status": "ATIVO",
                },
                {
                    "tipo_titulo": "LFT",
                    "data_vencimento": "2028-01-01",
                    "data_referencia": "2026-01-11",
                    "qtd_operacoes": 3,
                    "qtd_titulos": 50.0,
                    "pu_medio": 400.0,
                    "expressao": None,
                    "data_base": "2000-01-01",
                    "codigo_selic": "300000",
                    "codigo_isin": "BRSTNCNTF009",
                    "status": "ATIVO",
                },
            ]
        ),
        db_path=db,
    )
    reader = GoldReader(db_path=db)
    latest = reader.mercado_com_liquidacoes.fetch_latest(2)
    assert latest["data_referencia"].nunique() == 2
    assert set(latest["data_referencia"]) == {"2026-01-11", "2026-01-12"}
    assert len(latest) == 2
