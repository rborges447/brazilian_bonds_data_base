"""
Map raw SIDRA (IBGE) tables into canonical long format.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd


def _find_header_row(df: pd.DataFrame, *, expected_tokens: Iterable[str], max_scan_rows: int = 4) -> int | None:
    """
    Heuristic: SIDRA sometimes prepends metadata rows.
    Scan the first rows for a row that contains all expected header labels.
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
    Convert raw sidrapy DataFrame into the canonical IPCA "long" schema.

    Output columns:
      - DATA, DATA_CODIGO, MEDIDA, VAR_CODIGO, VALOR
    """
    if df_sidra is None or df_sidra.empty:
        return pd.DataFrame(columns=["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"])

    df0 = df_sidra.copy()

    # 1) Header row (notebook equivalent, with extra robustness)
    expected_tokens = ["Mês", "Mês (Código)", "Variável (Código)", "Unidade de Medida", "Valor"]
    header_row = _find_header_row(df0, expected_tokens=expected_tokens)
    if header_row is None:
        header_row = 0

    df0.columns = df0.iloc[header_row]
    df0 = df0.drop(index=list(range(0, header_row + 1))).reset_index(drop=True)

    # 2) Validate base columns before filtering
    required_cols = ["Mês", "Mês (Código)", "Variável (Código)", "Unidade de Medida", "Valor"]
    missing = [c for c in required_cols if c not in df0.columns]
    if missing:
        raise ValueError(
            "SIDRA IPCA: unexpected layout after header detection. "
            f"Missing columns={missing}. Found columns={list(df0.columns)}"
        )

    # 3) Filter variables (2266 index level, 63 monthly change)
    var_codes = df0["Variável (Código)"].astype("string").str.strip()
    df0 = df0[var_codes.isin({"2266", "63"})].copy()

    if df0.empty:
        return pd.DataFrame(columns=["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"])

    # 4) Select columns
    df0 = df0[["Mês", "Mês (Código)", "Unidade de Medida", "Variável (Código)", "Valor"]].copy()

    # 5) Rename
    df0 = df0.rename(
        columns={
            "Mês": "DATA",
            "Mês (Código)": "DATA_CODIGO",
            "Unidade de Medida": "MEDIDA",
            "Variável (Código)": "VAR_CODIGO",
            "Valor": "VALOR",
        }
    )

    # 6) Types: DATA_CODIGO string, VALOR float
    df0["DATA_CODIGO"] = df0["DATA_CODIGO"].astype("string").str.strip()
    df0["VAR_CODIGO"] = df0["VAR_CODIGO"].astype("string").str.strip()
    df0["MEDIDA"] = df0["MEDIDA"].astype("string").str.strip()

    s = df0["VALOR"].astype("string").str.strip()
    # If comma decimals: drop thousands '.' then swap ',' -> '.'
    if s.str.contains(",", na=False).any():
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    df0["VALOR"] = pd.to_numeric(s, errors="coerce").astype(float)

    return df0.reset_index(drop=True)
