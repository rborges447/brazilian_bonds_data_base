from __future__ import annotations

import pandas as pd

from app.lake.silver.transforms.vna import normalize_from_records, normalize_partition

_REF_DATE = "2025-05-26"
_OTHER_DATE = "2025-05-27"
_VNA_PAYLOAD = [
    {
        "data_referencia": _REF_DATE,
        "titulos": [
            {
                "tipo_titulo": "LFT",
                "codigo_selic": "210100",
                "index": 14.65,
                "tipo_correcao": "O",
                "data_validade": "2025-05-23",
                "vna": 16616.592308,
            }
        ],
    }
]


def test_normalize_from_records_real_payload() -> None:
    out = normalize_from_records(_VNA_PAYLOAD)
    assert list(out.columns) == [
        "data_referencia",
        "codigo_selic",
        "tipo_correcao",
        "index",
        "data_validade",
        "vna",
    ]
    assert len(out) == 1
    assert out.iloc[0]["data_referencia"] == _REF_DATE
    assert out.iloc[0]["codigo_selic"] == 210100
    assert out.iloc[0]["tipo_correcao"] == "O"
    assert out.iloc[0]["index"] == 14.65
    assert out.iloc[0]["data_validade"] == "2025-05-23"
    assert out.iloc[0]["vna"] == 16616.592308


def test_codigo_selic_string_becomes_int() -> None:
    records = [
        {
            "data_referencia": _REF_DATE,
            "titulos": [
                {
                    "codigo_selic": "210100",
                    "tipo_correcao": "O",
                    "index": 1.0,
                    "data_validade": "2025-05-23",
                    "vna": 100.0,
                }
            ],
        }
    ]
    out = normalize_from_records(records)
    assert out.iloc[0]["codigo_selic"] == 210100
    assert str(out["codigo_selic"].dtype) == "Int64"


def test_index_and_vna_comma_decimal() -> None:
    records = [
        {
            "data_referencia": _REF_DATE,
            "titulos": [
                {
                    "codigo_selic": "210100",
                    "tipo_correcao": "O",
                    "index": "14,65",
                    "data_validade": "2025-05-23",
                    "vna": "16616,59",
                }
            ],
        }
    ]
    out = normalize_from_records(records)
    assert out.iloc[0]["index"] == 14.65
    assert out.iloc[0]["vna"] == 16616.59


def test_normalize_partition_filters_by_partition_value() -> None:
    payload = [
        {
            "data_referencia": _REF_DATE,
            "titulos": [
                {
                    "codigo_selic": "210100",
                    "tipo_correcao": "O",
                    "index": 14.65,
                    "data_validade": "2025-05-23",
                    "vna": 16616.59,
                }
            ],
        },
        {
            "data_referencia": _OTHER_DATE,
            "titulos": [
                {
                    "codigo_selic": "210100",
                    "tipo_correcao": "O",
                    "index": 14.70,
                    "data_validade": "2025-05-24",
                    "vna": 16620.00,
                }
            ],
        },
    ]
    df_raw = pd.DataFrame(payload)
    out = normalize_partition(df_raw, _REF_DATE, None)
    assert len(out) == 1
    assert out.iloc[0]["data_referencia"] == _REF_DATE


def test_empty_payload_returns_empty_canonical_df() -> None:
    out_records = normalize_from_records([])
    assert list(out_records.columns) == [
        "data_referencia",
        "codigo_selic",
        "tipo_correcao",
        "index",
        "data_validade",
        "vna",
    ]
    assert len(out_records) == 0

    out_df = normalize_partition(pd.DataFrame(), _REF_DATE, None)
    assert list(out_df.columns) == list(out_records.columns)
    assert len(out_df) == 0


def test_normalize_partition_from_bronze_nested_df() -> None:
    df_raw = pd.json_normalize(_VNA_PAYLOAD)
    out = normalize_partition(df_raw, _REF_DATE, None)
    assert len(out) == 1
    assert out.iloc[0]["codigo_selic"] == 210100
    assert out.iloc[0]["vna"] == 16616.592308
