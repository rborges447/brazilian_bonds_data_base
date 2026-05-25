from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest


def test_import_app_public() -> None:
    importlib.import_module("app.public")


def test_public_exports() -> None:
    from app.public import read_data, update

    assert callable(update)
    assert callable(read_data)


def test_public_all_surface() -> None:
    import app.public

    assert set(app.public.__all__) == {"read_data", "update"}
    assert not hasattr(app.public, "GoldReader")
    assert not hasattr(app.public, "read_gold")


@patch("app.services.update_database_service.update_database")
def test_import_app_public_does_not_run_update(mock_update_database) -> None:
    for name in list(sys.modules):
        if name == "app.public" or name.startswith("app.public."):
            del sys.modules[name]
    importlib.import_module("app.public")
    mock_update_database.assert_not_called()

