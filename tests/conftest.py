"""Fixtures para testes de inspeção do data lake."""

from __future__ import annotations

import os
from datetime import date

import pytest

from rf_lake.settings import DATA_START_DATE


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: testes que leem data/raw, data/silver e data/app.db",
    )


@pytest.fixture(scope="session")
def start_date() -> str:
    return os.getenv("LAKE_INSPECT_START", DATA_START_DATE).strip()


@pytest.fixture(scope="session")
def end_date() -> str:
    return os.getenv("LAKE_INSPECT_END", date.today().isoformat()).strip()
