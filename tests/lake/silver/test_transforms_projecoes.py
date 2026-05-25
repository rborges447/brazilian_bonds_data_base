from __future__ import annotations

from app.lake.silver.transforms.projecoes import normalize_from_records, ref_month_to_iso


def test_ref_month_to_iso_slash_and_hyphen() -> None:
    assert ref_month_to_iso("05/2026") == "2026-05-01"
    assert ref_month_to_iso("05-2026") == "2026-05-01"


def test_normalize_keeps_all_revisions() -> None:
    records = [
        {
            "indice": "IPCA",
            "tipo_projecao": "PROJEÇÕES PARA O MÊS CORRENTE",
            "data_coleta": "2026-05-12",
            "mes_referencia": "05/2026",
            "variacao_projetada": 0.5,
            "data_validade": "2026-05-18",
        },
        {
            "indice": "IPCA",
            "tipo_projecao": "PROJEÇÕES PARA O MÊS CORRENTE",
            "data_coleta": "2026-05-19",
            "mes_referencia": "05/2026",
            "variacao_projetada": 0.55,
            "data_validade": "2026-05-20",
        },
        {
            "indice": "IPCA",
            "tipo_projecao": "PROJEÇÕES PARA O MÊS POSTERIOR",
            "data_coleta": "2026-05-12",
            "mes_referencia": "06/2026",
            "variacao_projetada": 0.33,
            "data_validade": None,
        },
        {
            "indice": "IGP-M",
            "tipo_projecao": "PROJEÇÕES PARA O MÊS CORRENTE",
            "data_coleta": "2026-05-12",
            "mes_referencia": "05/2026",
            "variacao_projetada": 0.7,
            "data_validade": "2026-05-13",
        },
    ]
    df = normalize_from_records(records)
    assert len(df) == 4
    assert set(df["ref_month"]) == {"2026-05-01", "2026-06-01"}
