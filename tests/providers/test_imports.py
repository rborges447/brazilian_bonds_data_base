from __future__ import annotations

import importlib


def test_providers_public_exports() -> None:
    pkg = importlib.import_module("app.providers")
    expected = {
        "AnbimaAuth",
        "AnbimaClient",
        "MERCADO_SECUNDARIO_TPF",
        "fetch_cdi_daily",
        "fetch_feriados",
        "fetch_ptax_usd",
        "fetch_negociacoes_bruto_por_datas",
        "get_resultados",
        "SidraIpcaClient",
        "scrap_ajustes_bmf",
    }
    for name in expected:
        assert hasattr(pkg, name), f"missing export: {name}"


def test_subpackages_import() -> None:
    for module in (
        "app.providers.anbima",
        "app.providers.feriados",
        "app.providers.bcb",
        "app.providers.tesouro",
        "app.providers.sidra",
        "app.providers.uptodata",
    ):
        importlib.import_module(module)
