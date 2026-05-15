"""
Mapeamento de dados do SIDRA (IBGE) para formato canônico.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd


def _find_header_row(df: pd.DataFrame, *, expected_tokens: Iterable[str], max_scan_rows: int = 4) -> int | None:
    """
    Heurística: o SIDRA às vezes retorna linhas iniciais de metadados.
    Procuramos, nas primeiras linhas, uma linha que contenha os nomes esperados de colunas.
    """
    if df is None or df.empty:
        return None

    expected = {str(t).strip() for t in expected_tokens if str(t).strip()}
    scan = min(max_scan_rows, len(df))
    for i in range(scan):
        row_vals = {str(v).strip() for v in df.iloc[i].tolist() if pd.notna(v)}
        if expected.issubset(row_vals):
            return i
    return None


def sidra_ipca_to_long(df_sidra: pd.DataFrame) -> pd.DataFrame:
    """
    Converte o DataFrame bruto do sidrapy (SIDRA) para formato "long" canônico do IPCA.

    Retorna colunas exatas:
      - DATA, DATA_CODIGO, MEDIDA, VAR_CODIGO, VALOR
    """
    if df_sidra is None or df_sidra.empty:
        return pd.DataFrame(columns=["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"])

    df0 = df_sidra.copy()

    # 1) Ajuste de cabeçalho (equivalente ao notebook, mas com heurística para maior robustez)
    expected_tokens = ["Mês", "Mês (Código)", "Variável (Código)", "Unidade de Medida", "Valor"]
    header_row = _find_header_row(df0, expected_tokens=expected_tokens)
    if header_row is None:
        # fallback: comportamento do notebook (assume header na primeira linha)
        header_row = 0

    df0.columns = df0.iloc[header_row]
    df0 = df0.drop(index=list(range(0, header_row + 1))).reset_index(drop=True)

    # 2) Validar colunas base antes de filtrar
    required_cols = ["Mês", "Mês (Código)", "Variável (Código)", "Unidade de Medida", "Valor"]
    missing = [c for c in required_cols if c not in df0.columns]
    if missing:
        raise ValueError(
            "SIDRA IPCA: layout inesperado após ajuste de cabeçalho. "
            f"Colunas ausentes={missing}. Colunas encontradas={list(df0.columns)}"
        )

    # 3) Filtra variáveis (2266 número-índice, 63 variação mensal)
    var_codes = df0["Variável (Código)"].astype("string").str.strip()
    df0 = df0[var_codes.isin({"2266", "63"})].copy()

    if df0.empty:
        return pd.DataFrame(columns=["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"])

    # 4) Seleciona colunas
    df0 = df0[["Mês", "Mês (Código)", "Unidade de Medida", "Variável (Código)", "Valor"]].copy()

    # 5) Renomeia
    df0 = df0.rename(
        columns={
            "Mês": "DATA",
            "Mês (Código)": "DATA_CODIGO",
            "Unidade de Medida": "MEDIDA",
            "Variável (Código)": "VAR_CODIGO",
            "Valor": "VALOR",
        }
    )

    # 6) Tipos: DATA_CODIGO string, VALOR float
    df0["DATA_CODIGO"] = df0["DATA_CODIGO"].astype("string").str.strip()
    df0["VAR_CODIGO"] = df0["VAR_CODIGO"].astype("string").str.strip()
    df0["MEDIDA"] = df0["MEDIDA"].astype("string").str.strip()

    s = df0["VALOR"].astype("string").str.strip()
    # Se vier com vírgula decimal, remove milhares (.) e troca ',' por '.'
    if s.str.contains(",", na=False).any():
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    df0["VALOR"] = pd.to_numeric(s, errors="coerce").astype(float)

    return df0.reset_index(drop=True)

