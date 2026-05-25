"""Map raw SIDRA (sidrapy) tables into canonical IPCA long format."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

VAR_IPCA_INDEX = "2266"
VAR_IPCA_MOM = "63"


def _find_header_row(
    df: pd.DataFrame, *, expected_tokens: Iterable[str], max_scan_rows: int = 4
) -> int | None:
    if df is None or df.empty:
        return None
    expected = {str(t).strip() for t in expected_tokens if str(t).strip()}
    scan = min(max_scan_rows, len(df))
    for i in range(scan):
        row_vals = {str(v).strip() for v in df.iloc[i].tolist() if pd.notna(v)}
        if expected.issubset(row_vals):
            return i
    return None


def _sidra_abbreviated_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """sidrapy columns: D2C (YYYYMM), D3C (var code), V (value)."""
    var_col = None
    for candidate in ("D3C", "Variável (Código)", "VAR_CODIGO"):
        if candidate in df.columns:
            var_col = candidate
            break
    if var_col is None:
        raise ValueError(
            "SIDRA IPCA: abbreviated layout requires variable code column (D3C)."
        )

    out = df.copy()
    out = out.rename(
        columns={
            "D2C": "DATA_CODIGO",
            var_col: "VAR_CODIGO",
            "V": "VALOR",
        }
    )
    if "Mês" in df.columns:
        out["DATA"] = df["Mês"]
    elif "D2N" in df.columns:
        out["DATA"] = df["D2N"]
    else:
        out["DATA"] = None

    if "D3N" in df.columns:
        out["MEDIDA"] = df["D3N"]
    elif "Unidade de Medida" in df.columns:
        out["MEDIDA"] = df["Unidade de Medida"]
    else:
        out["MEDIDA"] = None

    var_codes = out["VAR_CODIGO"].astype("string").str.strip()
    out = out[var_codes.isin({VAR_IPCA_INDEX, VAR_IPCA_MOM})].copy()
    if out.empty:
        return pd.DataFrame(columns=["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"])

    out["DATA_CODIGO"] = out["DATA_CODIGO"].astype("string").str.strip()
    out["VAR_CODIGO"] = out["VAR_CODIGO"].astype("string").str.strip()
    s = out["VALOR"].astype("string").str.strip()
    if s.str.contains(",", na=False).any():
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    out["VALOR"] = pd.to_numeric(s, errors="coerce").astype(float)
    return out[["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"]].reset_index(drop=True)


def sidra_ipca_to_long(df_sidra: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw sidrapy DataFrame into long schema:
    DATA, DATA_CODIGO, MEDIDA, VAR_CODIGO, VALOR.
    """
    if df_sidra is None or df_sidra.empty:
        return pd.DataFrame(columns=["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"])

    if "DATA_CODIGO" in df_sidra.columns and "VAR_CODIGO" in df_sidra.columns:
        out = df_sidra.copy()
        if "VALOR" not in out.columns and "V" in out.columns:
            out = out.rename(columns={"V": "VALOR"})
        cols = ["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"]
        for c in cols:
            if c not in out.columns:
                out[c] = None
        return out[cols].reset_index(drop=True)

    if "D2C" in df_sidra.columns and "V" in df_sidra.columns:
        return _sidra_abbreviated_to_long(df_sidra)

    df0 = df_sidra.copy()
    expected_tokens = ["Mês", "Mês (Código)", "Variável (Código)", "Unidade de Medida", "Valor"]
    header_row = _find_header_row(df0, expected_tokens=expected_tokens)
    if header_row is None:
        header_row = 0

    df0.columns = df0.iloc[header_row]
    df0 = df0.drop(index=list(range(0, header_row + 1))).reset_index(drop=True)

    required_cols = ["Mês", "Mês (Código)", "Variável (Código)", "Unidade de Medida", "Valor"]
    missing = [c for c in required_cols if c not in df0.columns]
    if missing:
        raise ValueError(
            "SIDRA IPCA: unexpected layout after header detection. "
            f"Missing columns={missing}. Found columns={list(df0.columns)}"
        )

    var_codes = df0["Variável (Código)"].astype("string").str.strip()
    df0 = df0[var_codes.isin({VAR_IPCA_INDEX, VAR_IPCA_MOM})].copy()
    if df0.empty:
        return pd.DataFrame(columns=["DATA", "DATA_CODIGO", "MEDIDA", "VAR_CODIGO", "VALOR"])

    df0 = df0[
        ["Mês", "Mês (Código)", "Unidade de Medida", "Variável (Código)", "Valor"]
    ].copy()
    df0 = df0.rename(
        columns={
            "Mês": "DATA",
            "Mês (Código)": "DATA_CODIGO",
            "Unidade de Medida": "MEDIDA",
            "Variável (Código)": "VAR_CODIGO",
            "Valor": "VALOR",
        }
    )
    df0["DATA_CODIGO"] = df0["DATA_CODIGO"].astype("string").str.strip()
    df0["VAR_CODIGO"] = df0["VAR_CODIGO"].astype("string").str.strip()
    s = df0["VALOR"].astype("string").str.strip()
    if s.str.contains(",", na=False).any():
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    df0["VALOR"] = pd.to_numeric(s, errors="coerce").astype(float)
    return df0.reset_index(drop=True)
