from __future__ import annotations

from datetime import date

import pandas as pd

# SIDRA variable codes (kept here to avoid normalizer ↔ client coupling)
VAR_IPCA_INDEX = "2266"  # index level
VAR_IPCA_MOM = "63"  # month-on-month change (%)


def ipca_long_to_monthly(df_long: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot long-format IPCA to monthly wide format (one row per month).

    Expected input columns:
      - DATA, DATA_CODIGO (YYYYMM), MEDIDA, VAR_CODIGO, VALOR

    Output columns:
      - ref_month: datetime.date (first day of month)
      - ipca_index: float (VAR 2266)
      - ipca_mom: float (VAR 63)

    Rules:
    - No duplicate collapse: more than one value per (month, variable) raises an error.
    - Sorted ascending by ref_month.
    """
    if df_long is None or df_long.empty:
        return pd.DataFrame(columns=["ref_month", "ipca_index", "ipca_mom"])

    df = df_long.copy()

    required_cols = ["DATA_CODIGO", "VAR_CODIGO", "VALOR"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"IPCA normalizer: missing columns in df_long: {missing}")

    df["DATA_CODIGO"] = df["DATA_CODIGO"].astype("string").str.strip()
    df["VAR_CODIGO"] = df["VAR_CODIGO"].astype("string").str.strip()

    # ref_month derivado de YYYYMM
    def _to_ref_month(yyyymm: str) -> date:
        s = str(yyyymm).strip()
        if len(s) != 6 or not s.isdigit():
            raise ValueError(f"IPCA normalizer: invalid DATA_CODIGO (expected YYYYMM): {yyyymm!r}")
        y = int(s[:4])
        m = int(s[4:6])
        return date(y, m, 1)

    df["ref_month"] = df["DATA_CODIGO"].map(_to_ref_month)

    # At most one row per (ref_month, VAR_CODIGO)
    counts = df.groupby(["ref_month", "VAR_CODIGO"], dropna=False).size()
    dup = counts[counts > 1]
    if not dup.empty:
        sample = dup.head(8)
        raise ValueError(f"IPCA normalizer: duplicate (month, variable) keys: {sample.to_dict()}")

    piv = df.pivot(index="ref_month", columns="VAR_CODIGO", values="VALOR")

    # Ensure columns even if a variable is missing for some slice
    if VAR_IPCA_INDEX not in piv.columns:
        piv[VAR_IPCA_INDEX] = pd.NA
    if VAR_IPCA_MOM not in piv.columns:
        piv[VAR_IPCA_MOM] = pd.NA

    out = piv[[VAR_IPCA_INDEX, VAR_IPCA_MOM]].rename(
        columns={
            VAR_IPCA_INDEX: "ipca_index",
            VAR_IPCA_MOM: "ipca_mom",
        }
    )

    out = out.reset_index()
    out = out.sort_values("ref_month", ascending=True).reset_index(drop=True)

    # Coerce float where possible
    out["ipca_index"] = pd.to_numeric(out["ipca_index"], errors="coerce").astype(float)
    out["ipca_mom"] = pd.to_numeric(out["ipca_mom"], errors="coerce").astype(float)

    return out[["ref_month", "ipca_index", "ipca_mom"]]

