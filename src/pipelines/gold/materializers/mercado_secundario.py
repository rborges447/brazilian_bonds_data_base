"""Mercado secundário: silver partitions → DataFrame ready for SQL INSERT."""

from __future__ import annotations

import pandas as pd

from pipelines.gold.contracts import BuilderContext, MercadoSecundarioGoldValue, SilverFrames
from pipelines.gold.materializers._tabular import SQL_STATUS_DEFAULT, prepare_tabular_output

_DATASET = "mercado_secundario"
_REQUIRED_SILVER = (
    "tipo_titulo",
    "data_vencimento",
    "data_referencia",
    "taxa_anbima",
    "intervalo_min_d0",
    "intervalo_max_d0",
    "intervalo_min_d1",
    "intervalo_max_d1",
    "pu",
)
_OPTIONAL_SILVER = (
    "expressao",
    "data_base",
    "codigo_selic",
    "codigo_isin",
    "taxa_compra",
    "taxa_venda",
    "desvio_padrao",
)
_SQL_DEFAULTS = {"status": SQL_STATUS_DEFAULT}
_OUTPUT_COLS = (
    *_REQUIRED_SILVER,
    *_OPTIONAL_SILVER,
    "status",
)
_EMPTY = pd.DataFrame(columns=list(_OUTPUT_COLS))
_DEDUP_SUBSET = ("data_referencia", "tipo_titulo", "data_vencimento")
_SORT_BY = ("data_referencia", "data_vencimento", "tipo_titulo")


def from_silver(silver: SilverFrames, ctx: BuilderContext) -> MercadoSecundarioGoldValue:
    """
    Filter silver mercado_secundario to ``ctx.dates`` and return rows for SQL insert.

    ``status`` is filled at gold when absent in silver (default ATIVO).
    """
    if ctx.dates is None:
        raise ValueError(
            "Mercado secundario materialization requires ctx.dates (list of ISO dates)."
        )
    if not ctx.dates:
        return _EMPTY.copy()

    if _DATASET not in silver:
        raise KeyError(
            f"Silver dataset '{_DATASET}' missing. Run bronze/silver for mercado_secundario first."
        )
    df = silver[_DATASET]
    if df is None or df.empty:
        raise ValueError(
            f"Silver mercado_secundario is empty for requested dates: {ctx.dates}. "
            "Run bronze/silver for those partitions."
        )

    requested = {d.strip()[:10] for d in ctx.dates}
    out = df.copy()
    out["data_referencia"] = out["data_referencia"].astype(str).str.strip().str[:10]
    out = out[out["data_referencia"].isin(requested)]
    out = prepare_tabular_output(
        out,
        dataset=_DATASET,
        required_silver=_REQUIRED_SILVER,
        optional_silver=_OPTIONAL_SILVER,
        sql_defaults=_SQL_DEFAULTS,
    )
    out = (
        out.drop_duplicates(subset=list(_DEDUP_SUBSET))
        .sort_values(list(_SORT_BY))
        .reset_index(drop=True)
    )

    found_dates = set(out["data_referencia"])
    missing_dates = sorted(requested - found_dates)
    if missing_dates:
        raise ValueError(
            f"Silver mercado_secundario has no rows for requested dates: {missing_dates}. "
            f"Loaded {len(df)} row(s) from silver."
        )
    return out
