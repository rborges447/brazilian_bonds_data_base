"""Facade to read all gold SQLite tables."""

from __future__ import annotations

from typing import Any

from app.database.readers._date_series import DateSeriesTableReader
from app.database.readers._mercado_liquidacoes import MercadoLiquidacoesReader
from app.database.readers._static import (
    ContratosBmfReader,
    FeriadosReader,
    TitulosPublicosReader,
)


class GoldReader:
    """
    Read persisted gold data as pandas DataFrames.

    Daily series (``fetch_latest``, ``fetch_on``, ``fetch_range``, ``fetch_all``):

    - ``cdi``, ``ptax``, ``ipca_dict``, ``mercado_secundario``, ``liquidacoes_mercado``,
      ``leiloes``, ``ajustes_bmf``

    ``fetch_latest(n)`` returns all rows for the last ``n`` distinct reference dates
    (not the last ``n`` physical rows).

    Snapshot tables (``fetch_all`` only):

    - ``feriados``, ``titulos_publicos``, ``contratos_bmf``

    Combined full outer:

    - ``mercado_com_liquidacoes`` (alias ``mercado_liquidacoes``)
    """

    def __init__(self, *, db_path: Any = None) -> None:
        self._db_path = db_path
        self.cdi = DateSeriesTableReader(query_prefix="cdi", db_path=db_path)
        self.ptax = DateSeriesTableReader(query_prefix="ptax", db_path=db_path)
        self.ipca_dict = DateSeriesTableReader(query_prefix="ipca_dict", db_path=db_path)
        self.mercado_secundario = DateSeriesTableReader(
            query_prefix="mercado_secundario", db_path=db_path
        )
        self.liquidacoes_mercado = DateSeriesTableReader(
            query_prefix="liquidacoes_mercado", db_path=db_path
        )
        self.leiloes = DateSeriesTableReader(query_prefix="leiloes", db_path=db_path)
        self.ajustes_bmf = DateSeriesTableReader(query_prefix="ajustes_bmf", db_path=db_path)
        self.feriados = FeriadosReader(db_path=db_path)
        self.titulos_publicos = TitulosPublicosReader(db_path=db_path)
        self.contratos_bmf = ContratosBmfReader(db_path=db_path)
        self.mercado_com_liquidacoes = MercadoLiquidacoesReader(db_path=db_path)
        self.mercado_liquidacoes = self.mercado_com_liquidacoes
