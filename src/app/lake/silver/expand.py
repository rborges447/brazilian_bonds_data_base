"""
Expand monthly silver/bronze partitions to business-day grain at read time.

Does not write daily partitions to disk.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from app.core.dates import business_days
from app.core.partitioning import get_partition_spec
from app.lake.bronze.reader import read_range as read_bronze_range
from app.lake.silver.reader import read_range as read_silver_range

_MONTHLY_DATASETS = frozenset({"ipca_indice", "projecoes"})


def _month_key(series: pd.Series) -> pd.Series:
    """Normalize ref_month / reference_month to YYYY-MM-01 strings."""
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed.dt.strftime("%Y-%m-01")


def read_monthly_as_daily(
    dataset: str,
    start: str,
    end: str,
    *,
    layer: Literal["silver", "bronze"] = "silver",
) -> pd.DataFrame:
    """
    Read monthly partitions and expand each month to all business days in range.

    Convention: the month's metric applies to every business day in that calendar month
  (not an observed daily series). Useful for joins with daily datasets.
    """
    if dataset not in _MONTHLY_DATASETS:
        raise ValueError(f"read_monthly_as_daily supports {_MONTHLY_DATASETS}, got {dataset!r}")

    spec = get_partition_spec(dataset)
    read_fn = read_silver_range if layer == "silver" else read_bronze_range
    monthly = read_fn(
        dataset,
        start,
        end,
        add_partition_column=True,
    )
    if monthly.empty:
        return pd.DataFrame()

    part_col = f"_partition_{spec.partition_key}"
    if part_col in monthly.columns:
        monthly["reference_month"] = _month_key(monthly[part_col])
    elif "ref_month" in monthly.columns:
        monthly["reference_month"] = _month_key(monthly["ref_month"])
    else:
        raise ValueError(f"{dataset}: cannot derive reference_month from columns {list(monthly.columns)}")

    days = business_days(start, end)
    if not days:
        return pd.DataFrame()

    daily = pd.DataFrame({"data_referencia": days})
    daily["reference_month"] = daily["data_referencia"].str[:7] + "-01"

    metric_cols = [c for c in monthly.columns if c not in (part_col, "reference_month")]
    merged = daily.merge(
        monthly,
        on="reference_month",
        how="left",
        suffixes=("", "_month"),
    )
    front = ["data_referencia", "reference_month"]
    rest = [c for c in metric_cols if c not in front]
    return merged[front + rest]
