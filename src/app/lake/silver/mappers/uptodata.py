"""UpToData BMF row filters (port of legacy uptodata.mapping)."""

from __future__ import annotations

import pandas as pd


def filtro_di_dap(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only DI/DAP contract rows."""
    if df is None or df.empty or "TckrSymb" not in df.columns:
        return df
    return df[df["TckrSymb"].str.startswith(("DAP", "DI1"))]
