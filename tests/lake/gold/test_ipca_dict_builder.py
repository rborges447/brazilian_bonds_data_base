from __future__ import annotations

import pandas as pd
import pytest

from app.lake.gold.builders.ipca_dict import (
    INDICE_IPCA_DATA_BASE,
    build_for_date,
    can_build_for_date,
    e_dia_util,
    fechado_ref_months,
    inicio_fim_mes_ipca,
    ipca_ref_months_available,
    projecao_for_as_of,
    slice_monthly_frames,
)
from app.lake.gold.materializers.ipca_dict import IPCA_DICT_COLUMNS, to_dataframe

_FERIADOS: set[str] = set()


def _ipca_monthly() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ref_month": "2026-03-01", "ipca_index": 100.0, "ipca_mom": 0.5},
            {"ref_month": "2026-04-01", "ipca_index": 101.0, "ipca_mom": 0.6},
        ]
    )


def _projecoes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "indice": "IPCA",
                "tipo_projecao": "PROJEÇÕES PARA O MÊS CORRENTE",
                "ref_month": "2026-05-01",
                "data_coleta": "2026-05-05",
                "data_validade": pd.NA,
                "variacao_projetada": 0.45,
            }
        ]
    )


def test_slice_monthly_frames_takes_last_n_months() -> None:
    full = _ipca_monthly()
    out = slice_monthly_frames(full, "2026-04-15", n=1)
    assert len(out) == 1
    assert out.iloc[0]["ref_month"] == pd.Timestamp("2026-04-01")


def test_build_for_date_before_dia_15_uses_fechado() -> None:
    d = build_for_date(
        "2026-05-10",
        ipca_monthly=_ipca_monthly(),
        projecoes=_projecoes(),
        feriados=_FERIADOS,
    )
    assert d["USA_FECHADO"] is True
    assert d["IPCA_USADO"] == pytest.approx(1.0)
    assert d["IPCA_PROJ"] == pytest.approx(0.45)
    assert d["REF_MONTH_ATUAL"] == "2026-04-01"
    assert d["INDICE_IPCA_DATA_BASE"] == INDICE_IPCA_DATA_BASE


def test_build_for_date_after_dia_15_uses_projecao() -> None:
    d = build_for_date(
        "2026-05-20",
        ipca_monthly=_ipca_monthly(),
        projecoes=_projecoes(),
        feriados=_FERIADOS,
    )
    assert d["USA_FECHADO"] is False
    assert d["IPCA_USADO"] == pytest.approx(0.45)


def test_inicio_fim_mes_ipca_may_2026() -> None:
    inicio, fim = inicio_fim_mes_ipca("2026-05-10", _FERIADOS)
    assert inicio == pd.Timestamp("2026-04-15")
    assert fim == pd.Timestamp("2026-05-15")


def test_to_dataframe_columns_and_usa_fechado_int() -> None:
    pairs = [
        (
            "2026-05-10",
            build_for_date(
                "2026-05-10",
                ipca_monthly=_ipca_monthly(),
                projecoes=_projecoes(),
                feriados=_FERIADOS,
            ),
        ),
    ]
    out = to_dataframe(pairs)
    assert list(out.columns) == list(IPCA_DICT_COLUMNS)
    assert out.iloc[0]["data_referencia"] == "2026-05-10"
    assert out.iloc[0]["usa_fechado"] == 1
    assert out.iloc[0]["ipca_usado"] == pytest.approx(1.0)


def test_to_dataframe_empty() -> None:
    out = to_dataframe([])
    assert out.empty
    assert list(out.columns) == list(IPCA_DICT_COLUMNS)


def test_e_dia_util_weekend() -> None:
    assert e_dia_util("2026-05-16", _FERIADOS) is False


def test_can_build_for_date_false_without_monthly_history() -> None:
    assert (
        can_build_for_date(
            "2026-01-02",
            ipca_monthly=_ipca_monthly(),
            projecoes=_projecoes(),
            feriados=_FERIADOS,
        )
        is False
    )


def test_can_build_for_date_true_when_covered() -> None:
    assert can_build_for_date(
        "2026-05-10",
        ipca_monthly=_ipca_monthly(),
        projecoes=_projecoes(),
        feriados=_FERIADOS,
    )


def test_ipca_ref_months_available_requires_ultimo_ref() -> None:
    ipca = _ipca_monthly()
    ultimo, anterior = fechado_ref_months("2026-05-10", "2026-05-05")
    assert ipca_ref_months_available(ipca, ultimo, anterior)
    assert not ipca_ref_months_available(
        ipca, pd.Timestamp("2026-01-01"), pd.Timestamp("2025-12-01")
    )


def test_can_build_false_when_fechado_ref_month_missing() -> None:
    assert not can_build_for_date(
        "2026-01-02",
        ipca_monthly=_ipca_monthly(),
        projecoes=_projecoes(),
        feriados=_FERIADOS,
    )


def _ipca_monthly_with_lookback() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ref_month": "2025-11-01", "ipca_index": 98.0, "ipca_mom": 0.4},
            {"ref_month": "2025-12-01", "ipca_index": 99.0, "ipca_mom": 0.45},
            {"ref_month": "2026-01-01", "ipca_index": 99.5, "ipca_mom": 0.48},
            {"ref_month": "2026-02-01", "ipca_index": 100.0, "ipca_mom": 0.5},
            {"ref_month": "2026-03-01", "ipca_index": 100.5, "ipca_mom": 0.52},
            {"ref_month": "2026-04-01", "ipca_index": 101.0, "ipca_mom": 0.6},
        ]
    )


def _projecoes_jan() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "indice": "IPCA",
                "tipo_projecao": "PROJEÇÕES PARA O MÊS CORRENTE",
                "ref_month": "2026-01-01",
                "data_coleta": "2026-01-08",
                "data_validade": pd.NA,
                "variacao_projetada": 0.40,
            }
        ]
    )


def test_build_for_date_jan_with_ipca_lookback() -> None:
    d = build_for_date(
        "2026-01-15",
        ipca_monthly=_ipca_monthly_with_lookback(),
        projecoes=_projecoes_jan(),
        feriados=_FERIADOS,
    )
    assert "IPCA_USADO" in d
    assert d["REF_MONTH_ATUAL"] == "2025-12-01"


def test_projecao_for_as_of_weekend_uses_latest_coleta() -> None:
    proj = pd.DataFrame(
        [
            {
                "indice": "IPCA",
                "tipo_projecao": "PROJEÇÕES PARA O MÊS CORRENTE",
                "ref_month": "2026-02-01",
                "data_coleta": "2026-02-05",
                "data_validade": pd.NA,
                "variacao_projetada": 0.50,
            }
        ]
    )
    row = projecao_for_as_of(proj, "2026-02-01", respeitar_validade=False)
    assert row["data_coleta"] == pd.Timestamp("2026-02-05")
