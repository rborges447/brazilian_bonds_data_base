"""BCB SGS (Sistema Gerenciador de Séries Temporais) JSON API client."""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pandas as pd
import requests

from config import BcbSettings, get_settings
from providers.base import DateInput, ensure_date

logger = logging.getLogger(__name__)

_EMPTY_COLUMNS = ["data", "valor"]


def _format_bcb_dmy(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, month=2, day=28)


def _split_period_in_10y_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into contiguous windows of at most ~10 calendar years."""
    if start > end:
        raise ValueError("start date cannot be after end date.")

    chunks: list[tuple[date, date]] = []
    current_start = start

    while current_start <= end:
        chunk_end = min(_add_years(current_start, 10) - timedelta(days=1), end)
        chunks.append((current_start, chunk_end))
        current_start = chunk_end + timedelta(days=1)

    return chunks


def build_sgs_url(
    series_id: int,
    start_date: DateInput,
    end_date: DateInput,
    settings: BcbSettings | None = None,
) -> str:
    """Build BCB SGS JSON URL with dataInicial/dataFinal in DD/MM/YYYY."""
    cfg = settings or get_settings().bcb
    start_dt = ensure_date(start_date)
    end_dt = ensure_date(end_date)
    start_fmt = _format_bcb_dmy(start_dt)
    end_fmt = _format_bcb_dmy(end_dt)
    return (
        f"{cfg.sgs_base_url}.{series_id}/dados?"
        f"formato=json&dataInicial={start_fmt}&dataFinal={end_fmt}"
    )


def _replace_url_dates(url: str, start_date: date, end_date: date) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["dataInicial"] = [_format_bcb_dmy(start_date)]
    query["dataFinal"] = [_format_bcb_dmy(end_date)]
    new_query = urlencode(query, doseq=True)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )


def _fetch_chunk_json(url: str, timeout: int, max_retries: int) -> list[dict]:
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise TypeError(f"BCB SGS: expected JSON list, got {type(data).__name__}")
            return data
        except Exception as ex:
            last_err = ex
            if attempt < max_retries:
                logger.warning(
                    "BCB SGS: attempt %s/%s failed for %s: %s",
                    attempt,
                    max_retries,
                    url,
                    ex,
                )
                time.sleep(0.6 * attempt)
    assert last_err is not None
    raise last_err


def _records_to_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    return df


def fetch_bcb_sgs_series(
    series_id: int,
    start_date: DateInput | None = None,
    end_date: DateInput | None = None,
    settings: BcbSettings | None = None,
) -> pd.DataFrame:
    """
    Fetch a BCB SGS series as a DataFrame with columns ``data`` and ``valor``.

    Long ranges are requested in ~10-year chunks (API practical limit).
    """
    cfg = settings or get_settings().bcb
    app = get_settings()

    end_dt = ensure_date(end_date) if end_date is not None else date.today()
    start_dt = ensure_date(start_date) if start_date is not None else app.data_start_date

    if start_dt > end_dt:
        raise ValueError("start_date cannot be after end_date.")

    base_url = build_sgs_url(series_id, start_dt, end_dt, settings=cfg)
    chunks = _split_period_in_10y_chunks(start_dt, end_dt)

    frames: list[pd.DataFrame] = []
    for chunk_start, chunk_end in chunks:
        chunk_url = _replace_url_dates(base_url, chunk_start, chunk_end)
        try:
            records = _fetch_chunk_json(chunk_url, cfg.timeout, cfg.max_retries)
        except Exception as ex:
            logger.warning("BCB SGS: chunk failed %s to %s: %s", chunk_start, chunk_end, ex)
            raise

        if not records:
            logger.debug("BCB SGS: empty chunk %s to %s", chunk_start, chunk_end)
            continue

        df_chunk = _records_to_dataframe(records)
        if not df_chunk.empty:
            frames.append(df_chunk)

    if not frames:
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    df_final = pd.concat(frames, ignore_index=True)
    df_final = (
        df_final.drop_duplicates(subset=["data"])
        .sort_values("data")
        .reset_index(drop=True)
    )
    return df_final
