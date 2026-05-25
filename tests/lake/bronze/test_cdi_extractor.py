from __future__ import annotations



from pathlib import Path

from unittest.mock import patch



import pandas as pd



from app.lake.bronze.extractors.cdi import extract_cdi

from app.lake.bronze.paths import bronze_partition_path





def _anbima_frame(day: str, rate: float) -> pd.DataFrame:

    return pd.DataFrame(

        {

            "data_referencia": pd.to_datetime([day]),

            "estimativa_taxa_selic": [rate],

        }

    )





@patch("app.lake.bronze.extractors.cdi.fetch_estimativa_selic")

def test_extract_cdi_writes_partitions(mock_fetch, bronze_tmp_root: Path) -> None:

    mock_fetch.side_effect = [

        _anbima_frame("2026-01-15", 14.75),

        _anbima_frame("2026-01-16", 14.76),

    ]



    result = extract_cdi(["2026-01-15", "2026-01-16"])



    assert result.row_count == 2

    assert set(result.segment_keys) == {"2026-01-15", "2026-01-16"}

    assert mock_fetch.call_count == 2

    mock_fetch.assert_any_call("2026-01-15")

    mock_fetch.assert_any_call("2026-01-16")



    for day in ("2026-01-15", "2026-01-16"):

        path = bronze_partition_path("cdi", "data", day, "parquet")

        assert path.is_file()

        df = pd.read_parquet(path)

        assert list(df.columns) == ["data_referencia", "estimativa_taxa_selic"]

        assert len(df) == 1





@patch("app.lake.bronze.extractors.cdi.fetch_estimativa_selic")

def test_extract_cdi_skips_existing_partitions(mock_fetch, bronze_tmp_root: Path) -> None:

    existing = bronze_partition_path("cdi", "data", "2026-01-15", "parquet")

    existing.parent.mkdir(parents=True, exist_ok=True)

    _anbima_frame("2026-01-15", 14.75).to_parquet(existing, index=False)



    mock_fetch.return_value = _anbima_frame("2026-01-16", 14.76)



    result = extract_cdi(["2026-01-15", "2026-01-16"])



    assert result.segment_keys == ["2026-01-16"]

    mock_fetch.assert_called_once_with("2026-01-16")





@patch("app.lake.bronze.extractors.cdi.fetch_estimativa_selic")

def test_extract_cdi_empty_provider_response(mock_fetch, bronze_tmp_root: Path) -> None:

    mock_fetch.return_value = pd.DataFrame(columns=["data_referencia", "estimativa_taxa_selic"])



    result = extract_cdi(["2026-01-15"])



    assert result.row_count == 0

    assert result.segment_keys == []

    assert result.path is None

