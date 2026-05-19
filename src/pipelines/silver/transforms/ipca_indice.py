from __future__ import annotations

from datetime import date

import pandas as pd

from pipelines.silver.mappers.sidra_ipca import VAR_IPCA_INDEX, VAR_IPCA_MOM, sidra_ipca_to_long


def ipca_long_to_monthly(df_long: pd.DataFrame) -> pd.DataFrame:
    """Pivot long-format IPCA to one row per ref_month."""
    if df_long is None or df_long.empty:
        return pd.DataFrame(columns=["ref_month", "ipca_index", "ipca_mom"])

    df = df_long.copy()
    required_cols = ["DATA_CODIGO", "VAR_CODIGO", "VALOR"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"IPCA normalizer: missing columns in df_long: {missing}")

    df["DATA_CODIGO"] = df["DATA_CODIGO"].astype("string").str.strip()
    df["VAR_CODIGO"] = df["VAR_CODIGO"].astype("string").str.strip()

    def _to_ref_month(yyyymm: str) -> date:
        s = str(yyyymm).strip()
        if len(s) != 6 or not s.isdigit():
            raise ValueError(f"IPCA normalizer: invalid DATA_CODIGO (expected YYYYMM): {yyyymm!r}")
        return date(int(s[:4]), int(s[4:6]), 1)

    df["ref_month"] = df["DATA_CODIGO"].map(_to_ref_month)

    counts = df.groupby(["ref_month", "VAR_CODIGO"], dropna=False).size()
    dup = counts[counts > 1]
    if not dup.empty:
        raise ValueError(f"IPCA normalizer: duplicate (month, variable) keys: {dup.head(8).to_dict()}")

    piv = df.pivot(index="ref_month", columns="VAR_CODIGO", values="VALOR")
    if VAR_IPCA_INDEX not in piv.columns:
        piv[VAR_IPCA_INDEX] = pd.NA
    if VAR_IPCA_MOM not in piv.columns:
        piv[VAR_IPCA_MOM] = pd.NA

    out = piv[[VAR_IPCA_INDEX, VAR_IPCA_MOM]].rename(
        columns={VAR_IPCA_INDEX: "ipca_index", VAR_IPCA_MOM: "ipca_mom"}
    )
    out = out.reset_index().sort_values("ref_month", ascending=True).reset_index(drop=True)
    out["ipca_index"] = pd.to_numeric(out["ipca_index"], errors="coerce").astype(float)
    out["ipca_mom"] = pd.to_numeric(out["ipca_mom"], errors="coerce").astype(float)
    return out[["ref_month", "ipca_index", "ipca_mom"]]


def normalize_partition(
    df_raw: pd.DataFrame,
    partition_value: str,
    dates: list[str] | None = None,
) -> pd.DataFrame:
    del dates
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=["ref_month", "ipca_index", "ipca_mom"])
    df_long = sidra_ipca_to_long(df_raw)
    if df_long.empty:
        return pd.DataFrame(columns=["ref_month", "ipca_index", "ipca_mom"])
    monthly = ipca_long_to_monthly(df_long)
    if partition_value and not monthly.empty:
        target = date.fromisoformat(partition_value[:10])
        monthly = monthly[monthly["ref_month"] == target].copy()
    return monthly
