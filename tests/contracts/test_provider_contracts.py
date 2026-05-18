from __future__ import annotations

import inspect
from typing import get_origin, get_type_hints

import pandas as pd

from config.settings import AnbimaSettings
from contracts import (
    AnbimaFeedClient,
    DateRangeDataFrameFetcher,
    DateRangeRecordFetcher,
    SidraIpcaProvider,
    SnapshotDataFrameFetcher,
    SnapshotDateListFetcher,
)
from providers.anbima import AnbimaClient
from providers.bcb import fetch_negociacoes_bruto_por_datas
from providers.feriados import fetch_feriados
from providers.sidra import SidraIpcaClient
from providers.tesouro import get_resultados_by_dates
from providers.uptodata import scrap_ajustes_bmf_for_dates


def _first_param_accepts_sequence(fn: object) -> bool:
    sig = inspect.signature(fn)  # type: ignore[arg-type]
    params = list(sig.parameters.values())
    if not params:
        return False
    first = params[0].name
    return first in ("datas", "dates", "lista_datas")


def _callable_return_is_dataframe(fn: object) -> bool:
    hints = get_type_hints(fn)  # type: ignore[arg-type]
    return hints.get("return") is pd.DataFrame


def test_anbima_client_satisfies_protocol() -> None:
    cfg = AnbimaSettings(client_id="cid", client_secret="secret")
    client = AnbimaClient(settings=cfg)
    assert isinstance(client, AnbimaFeedClient)


def test_sidra_client_satisfies_protocol() -> None:
    client = SidraIpcaClient(max_retries=1)
    assert isinstance(client, SidraIpcaProvider)


def test_date_range_dataframe_fetchers() -> None:
    for fn in (fetch_negociacoes_bruto_por_datas, scrap_ajustes_bmf_for_dates):
        assert _first_param_accepts_sequence(fn)
        assert _callable_return_is_dataframe(fn)
    alias_origin = get_origin(DateRangeDataFrameFetcher)
    assert alias_origin is not None


def test_snapshot_date_list_fetcher() -> None:
    sig = inspect.signature(fetch_feriados)
    assert len(sig.parameters) == 0 or all(
        p.default is not inspect.Parameter.empty or p.name == "settings"
        for p in sig.parameters.values()
    )
    assert get_origin(get_type_hints(fetch_feriados).get("return")) is list


def test_date_range_record_fetcher() -> None:
    sig = inspect.signature(get_resultados_by_dates)
    assert "dates" in sig.parameters
    assert get_origin(get_type_hints(get_resultados_by_dates).get("return")) is list


def test_snapshot_dataframe_fetcher_alias() -> None:
    assert get_origin(SnapshotDataFrameFetcher) is not None
