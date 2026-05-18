"""Client for BCB (Brazilian Central Bank) trade settlement files."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from typing import Iterable, List, Union

import pandas as pd

from config import BcbSettings, get_settings
from providers.base import ensure_date

logger = logging.getLogger(__name__)

DateRef = Union[str, date]


def format_ano_mes(data_ref: DateRef) -> str:
    """Format date as YYYYMM for BCB NegE{YYYYMM}.ZIP files."""
    dt = ensure_date(data_ref)
    return f"{dt.year}{dt.month:02d}"


def build_negociacoes_url(
    data_ref: DateRef,
    base_url: str | None = None,
    settings: BcbSettings | None = None,
) -> str:
    cfg = settings or get_settings().bcb
    base = base_url if base_url is not None else cfg.base_url
    ano_mes = format_ano_mes(data_ref)
    return f"{base}/NegE{ano_mes}.ZIP"


def fetch_negociacoes_bruto_por_datas(
    datas: Iterable[DateRef],
    sep: str = ";",
    encoding: str = "latin-1",
    compression: str = "zip",
    date_column: str | None = None,
    base_url: str | None = None,
    settings: BcbSettings | None = None,
) -> pd.DataFrame:
    """
    Read raw BCB NegE{YYYYMM}.ZIP settlement CSVs across many calendar dates,
    retaining only rows for the dates requested.
    """
    cfg = settings or get_settings().bcb
    base = base_url if base_url is not None else cfg.base_url

    target_dates = {ensure_date(d) for d in datas}
    if not target_dates:
        return pd.DataFrame()

    dates_by_month: defaultdict[tuple[int, int], list[date]] = defaultdict(list)
    for dt in target_dates:
        dates_by_month[(dt.year, dt.month)].append(dt)

    frames: List[pd.DataFrame] = []

    def _parse_dates_disambiguate_slash(series: pd.Series, allowed: set[date]) -> pd.Series:
        s = series.copy()
        s_str = s.astype("string").str.strip()
        s_str = s_str.where(s_str.notna() & (s_str != ""), other=pd.NA)

        dt_dmy = pd.to_datetime(s_str, format="%d/%m/%Y", errors="coerce")
        dt_mdy = pd.to_datetime(s_str, format="%m/%d/%Y", errors="coerce")
        dt_iso = pd.to_datetime(s_str, format="%Y-%m-%d", errors="coerce")

        chosen = dt_iso.copy()
        dmy_ok = dt_dmy.dt.date.isin(allowed)
        mdy_ok = dt_mdy.dt.date.isin(allowed)
        chosen = chosen.where(~dmy_ok, dt_dmy)
        chosen = chosen.where(dmy_ok | ~mdy_ok, dt_mdy)
        fallback = dt_dmy.combine_first(dt_mdy)
        return chosen.combine_first(fallback)

    for (_year, _month), month_dates in dates_by_month.items():
        sample_date = month_dates[0]
        url = build_negociacoes_url(sample_date, base_url=base, settings=cfg)

        try:
            df_month = pd.read_csv(url, sep=sep, encoding=encoding, compression=compression)
        except Exception as ex:
            logger.warning("BCB settlements: failed to read %s: %s", url, ex)
            continue

        if df_month is None or df_month.empty:
            logger.warning("BCB settlements: empty response for %s", url)
            continue

        date_col = date_column
        if date_col is None:
            possible_names = [
                "data",
                "DATA",
                "Data Negociação",
                "DataNegociacao",
                "data_negociacao",
                "DtNeg",
                "dt_neg",
            ]
            for col in df_month.columns:
                if col.strip() in possible_names or "data" in col.lower():
                    date_col = col
                    break

        if date_col is None or date_col not in df_month.columns:
            logger.warning(
                "BCB settlements: date column not found in %s. Columns: %s",
                url,
                list(df_month.columns),
            )
            if date_column is not None:
                continue
            frames.append(df_month)
            continue

        allowed = set(month_dates)
        df_month[date_col] = _parse_dates_disambiguate_slash(df_month[date_col], allowed)
        df_month["_date_only"] = df_month[date_col].dt.date
        df_filtered = df_month[df_month["_date_only"].isin(month_dates)].copy()
        df_filtered = df_filtered.drop(columns=["_date_only"])

        if not df_filtered.empty:
            frames.append(df_filtered)

    if not frames:
        logger.info("BCB settlements: no rows after date filter; returning empty DataFrame.")
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True, sort=False)
