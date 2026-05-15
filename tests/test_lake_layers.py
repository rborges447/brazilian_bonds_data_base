"""
Testes de inspeção Bronze / Silver / Gold.

Exibem head() e dtypes por dataset e camada. Use pytest -s para ver o output:

    pip install -e ".[dev]"
    pytest tests/test_lake_layers.py -s -m integration
    pytest tests/test_lake_layers.py -s -k mercado_secundario

Intervalo customizado (PowerShell):

    $env:LAKE_INSPECT_START="2026-01-01"
    $env:LAKE_INSPECT_END="2026-01-10"
    pytest tests/test_lake_layers.py -s -m integration
"""

from __future__ import annotations

import pytest

from rf_lake.datasets import DATASETS
from rf_lake.inspect_layers import (
    all_layers_summary,
    format_layer_report,
    read_layer_range,
)

LAYERS = ("bronze", "silver", "gold")
DATASET_NAMES = tuple(DATASETS.keys())


@pytest.mark.integration
@pytest.mark.parametrize("layer", LAYERS)
@pytest.mark.parametrize("dataset", DATASET_NAMES)
def test_layer_dataframe_preview(layer, dataset, start_date, end_date):
    df = read_layer_range(layer, dataset, start_date, end_date)

    if df.empty:
        pytest.skip(f"sem dados em {layer}/{dataset} entre {start_date} e {end_date}")

    report = format_layer_report(
        layer, dataset, df, start_date=start_date, end_date=end_date
    )
    print(report)

    assert df is not None
    assert len(df.columns) > 0


@pytest.mark.integration
def test_all_layers_summary(start_date, end_date):
    summary = all_layers_summary(start_date, end_date)
    print("\n--- resumo todas as camadas ---\n")
    print(summary.to_string(index=False))

    assert not summary.empty
    assert "dataset" in summary.columns
    assert "layer" in summary.columns
