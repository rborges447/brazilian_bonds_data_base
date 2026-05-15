"""
Client for BCB (Banco Central do Brasil) trade files.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Iterable, List, Union

import pandas as pd

from rf_lake.logging import get_logger

logger = get_logger(__name__)

# Base URL for BCB trade downloads
DEFAULT_BASE_URL = "https://www4.bcb.gov.br/pom/demab/negociacoes/download"


def _ensure_date(data_ref: Union[str, date]) -> date:
    """
    Coerce input to datetime.date.

    Accepts:
      - str 'YYYY-MM-DD'
      - datetime.date
    """
    if isinstance(data_ref, date):
        return data_ref
    if isinstance(data_ref, str):
        try:
            return datetime.strptime(data_ref, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError("data_ref must be 'YYYY-MM-DD' (e.g. '2025-08-01').") from e
    raise TypeError("data_ref must be str ('YYYY-MM-DD') or datetime.date.")


def format_ano_mes(data_ref: Union[str, date]) -> str:
    """
    Format date as YYYYMM for Bacen NegE{YYYYMM}.ZIP files.
    Ex.: 2025-08-15 -> '202508'
    """
    dt = _ensure_date(data_ref)
    return f"{dt.year}{dt.month:02d}"


def build_negociacoes_url(data_ref: Union[str, date], base_url: str = DEFAULT_BASE_URL) -> str:
    """
    Build Bacen download URL for the monthly ZIP of trades.

    Input:
      - data_ref: 'YYYY-MM-DD' (str) or datetime.date
      - base_url: base URL (default: DEFAULT_BASE_URL)

    Output:
      - URL: {base_url}/NegE{YYYYMM}.ZIP
    """
    ano_mes = format_ano_mes(data_ref)
    return f"{base_url}/NegE{ano_mes}.ZIP"


def fetch_negociacoes_bruto_por_datas(
    datas: Iterable[Union[str, date]],
    sep: str = ";",
    encoding: str = "latin-1",
    compression: str = "zip",
    date_column: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
) -> pd.DataFrame:
    """
    Read raw Bacen NegE{YYYYMM}.ZIP trade files for many dates and keep only requested dates.

    Does **not** apply transforms beyond date filtering:
    - No general date parsing (except for filtering)
    - No column renames
    - No helper columns
    - No dtype coercion

    Behavior:
      - Group dates by month (avoid downloading the same ZIP repeatedly)
      - One ZIP download per distinct month
      - Filter rows to requested dates only
      - On read failure (404/network/empty file), log warning and continue
      - Concatenate only non-empty filtered frames
      - If nothing matches, return empty DataFrame

    Args:
      datas: iterable of 'YYYY-MM-DD' (str) or datetime.date
      sep: inner CSV separator (default ';')
      encoding: inner CSV encoding (default 'latin-1')
      compression: compression type (default 'zip' because endpoint is .ZIP)
      date_column: date column name (None = auto-detect)
      base_url: download base URL

    Returns:
      Raw concatenated DataFrame filtered to requested dates.
    """
    target_dates = {_ensure_date(d) for d in datas}
    if not target_dates:
        return pd.DataFrame()

    dates_by_month: defaultdict[tuple[int, int], list[date]] = defaultdict(list)

    for dt in target_dates:
        dates_by_month[(dt.year, dt.month)].append(dt)

    frames: List[pd.DataFrame] = []

    def _parse_dates_disambiguate_slash(series: pd.Series, allowed: set[date]) -> pd.Series:
        """
        Parse dates with DD/MM vs MM/DD ambiguity by picking, per row,
        the parse that falls in `allowed`.

        Some columns (e.g. DATA MOV) may arrive as '08/01/2017'; we must
        honor requested dates in `allowed`.
        """
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
        chosen = chosen.combine_first(fallback)

        return chosen

    for (year, month), month_dates in dates_by_month.items():
        sample_date = month_dates[0]
        url = build_negociacoes_url(sample_date, base_url)

        try:
            df_month = pd.read_csv(url, sep=sep, encoding=encoding, compression=compression)
        except Exception as ex:
            logger.warning("Bacen: failed to read %s: %s", url, ex)
            continue

        if df_month is None or df_month.empty:
            logger.warning("Bacen: empty response for %s", url)
            continue

        date_col = date_column
        if date_col is None:
            possible_names = ['data', 'DATA', 'Data Negociação', 'DataNegociacao',
                            'data_negociacao', 'DtNeg', 'dt_neg']
            for col in df_month.columns:
                if col.strip() in possible_names or 'data' in col.lower():
                    date_col = col
                    break

        if date_col is None or date_col not in df_month.columns:
            logger.warning(
                "Bacen: date column not found in %s. Columns: %s",
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

        df_filtered = df_month[df_month['_date_only'].isin(month_dates)].copy()
        df_filtered = df_filtered.drop(columns=['_date_only'])

        if not df_filtered.empty:
            frames.append(df_filtered)

    if not frames:
        logger.info("Bacen: no rows after date filter; returning empty DataFrame.")
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True, sort=False)
