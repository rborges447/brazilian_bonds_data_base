"""Shared helpers for tabular pass-through materializers."""

from __future__ import annotations

import pandas as pd

from app.lake.gold.contracts import BuilderContext

# Default for titulos_publicos when silver has no status column (legacy load).
SQL_STATUS_DEFAULT = "ATIVO"


def resolve_enforce_dates(
    ctx: BuilderContext,
    dataset: str,
    requested: set[str],
) -> tuple[set[str], list[str]]:
    """
    Dates that must have silver rows.

    When the orchestrator sets ``loaded_partitions_{dataset}`` (partitions that
    exist on disk), only those dates are enforced; requested dates without a
    partition are skipped (backfill / holidays / sparse ingest).
    """
    loaded_key = f"loaded_partitions_{dataset}"
    if loaded_key in ctx.extras:
        enforce = {d.strip()[:10] for d in ctx.extras[loaded_key]}
        skipped = sorted(requested - enforce)
        return enforce, skipped
    return requested, []


def raise_if_missing_enforced_dates(
    *,
    dataset: str,
    enforce_dates: set[str],
    found_dates: set[str],
    loaded_row_count: int,
    skipped_partitions: list[str],
) -> None:
    missing = sorted(enforce_dates - found_dates)
    if not missing:
        return
    suffix = (
        f" (no partition for: {skipped_partitions})" if skipped_partitions else ""
    )
    raise ValueError(
        f"Silver {dataset} has no rows for requested dates: {missing}. "
        f"Loaded {loaded_row_count} row(s) from silver.{suffix}"
    )


def prepare_tabular_output(
    df: pd.DataFrame,
    *,
    dataset: str,
    required_silver: tuple[str, ...],
    optional_silver: tuple[str, ...] = (),
    sql_defaults: dict[str, str] | None = None,
    output_columns: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """
    Select silver columns, apply SQL defaults, return frame ready for upsert.

    When ``output_columns`` is set, any column absent in silver is filled with
    ``None`` (SQL NULL) so persistence validators see the full gold schema.
    """
    for col in required_silver:
        if col not in df.columns:
            raise ValueError(
                f"Silver {dataset} must have column '{col}', got: {list(df.columns)}"
            )
    cols = list(required_silver)
    for col in optional_silver:
        if col in df.columns and col not in cols:
            cols.append(col)
    out = df[cols].copy()
    for col, value in (sql_defaults or {}).items():
        if col not in out.columns:
            out[col] = value
        if col not in cols:
            cols.append(col)
    if output_columns is None:
        return out[cols]
    for col in output_columns:
        if col not in out.columns:
            out[col] = None
    return out[list(output_columns)]
