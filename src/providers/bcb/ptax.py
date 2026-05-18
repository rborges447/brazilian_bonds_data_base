"""BCB PTAX closing rates (CSV export from ptax.bcb.gov.br)."""

from __future__ import annotations

import io
import logging
import re
import time
from datetime import date, timedelta
from urllib.parse import urlencode

import pandas as pd
import requests

from config import BcbSettings, get_settings
from providers.base import DateInput, ensure_date

logger = logging.getLogger(__name__)

_PTAX_METHOD = "gerarCSVFechamentoMoedaNoPeriodo"

_PTAX_COLUMNS = [
    "data_raw",
    "codigo",
    "tipo",
    "moeda",
    "taxa_compra",
    "taxa_venda",
    "paridade_compra",
    "paridade_venda",
]

_EMPTY_COLUMNS = [
    "data",
    "codigo",
    "tipo",
    "moeda",
    "taxa_compra",
    "taxa_venda",
    "paridade_compra",
    "paridade_venda",
]

_NUMERIC_COLUMNS = (
    "taxa_compra",
    "taxa_venda",
    "paridade_compra",
    "paridade_venda",
)

_PTAX_LINE_RE = re.compile(r"^\d{8};")
_SINGLE_DAY_LOOKBACK_DAYS = 14


def _format_bcb_dmy(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, month=2, day=28)


def _split_period_in_year_chunks(start: date, end: date) -> list[tuple[date, date]]:
    if start > end:
        raise ValueError("start date cannot be after end date.")

    chunks: list[tuple[date, date]] = []
    current_start = start

    while current_start <= end:
        chunk_end = min(_add_years(current_start, 1) - timedelta(days=1), end)
        chunks.append((current_start, chunk_end))
        current_start = chunk_end + timedelta(days=1)

    return chunks


def build_ptax_fechamento_url(
    start_date: DateInput,
    end_date: DateInput,
    moeda_code: int | None = None,
    settings: BcbSettings | None = None,
) -> str:
    """Build BCB PTAX closing CSV URL for a date range (DATAINI/DATAFIM as DD/MM/YYYY)."""
    cfg = settings or get_settings().bcb
    code = moeda_code if moeda_code is not None else cfg.ptax_moeda_code
    start_dt = ensure_date(start_date)
    end_dt = ensure_date(end_date)
    params = {
        "method": _PTAX_METHOD,
        "ChkMoeda": str(code),
        "DATAINI": _format_bcb_dmy(start_dt),
        "DATAFIM": _format_bcb_dmy(end_dt),
    }
    return f"{cfg.ptax_base_url}?{urlencode(params)}"


def _fetch_csv_text(url: str, timeout: int, max_retries: int) -> str:
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "latin-1"
            return response.text
        except Exception as ex:
            last_err = ex
            if attempt < max_retries:
                logger.warning(
                    "BCB PTAX: attempt %s/%s failed for %s: %s",
                    attempt,
                    max_retries,
                    url,
                    ex,
                )
                time.sleep(0.6 * attempt)
    assert last_err is not None
    raise last_err


def _normalize_decimal_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype("string").str.replace(",", ".", regex=False),
        errors="coerce",
    )


def _is_html_response(text: str) -> bool:
    head = text.lstrip()[:120].lower()
    return head.startswith("<!doctype") or head.startswith("<html")


def _extract_ptax_csv_body(text: str) -> str:
    """Keep only data lines (DDMMYYYY;...); ignore HTML or other noise."""
    lines = [line.strip() for line in text.splitlines() if _PTAX_LINE_RE.match(line.strip())]
    return "\n".join(lines)


def _csv_text_to_dataframe(text: str) -> pd.DataFrame:
    if _is_html_response(text):
        logger.warning("BCB PTAX: response is HTML, not CSV (often when DATAINI equals DATAFIM)")
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    csv_body = _extract_ptax_csv_body(text)
    if not csv_body:
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    df = pd.read_csv(
        io.StringIO(csv_body),
        sep=";",
        header=None,
        names=_PTAX_COLUMNS,
        dtype="string",
    )
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    df["data"] = pd.to_datetime(df["data_raw"], format="%d%m%Y", errors="coerce")
    for col in _NUMERIC_COLUMNS:
        df[col] = _normalize_decimal_series(df[col])

    df = df.drop(columns=["data_raw"]).dropna(subset=["data"])
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_COLUMNS)

    return df[_EMPTY_COLUMNS].reset_index(drop=True)


def fetch_ptax_fechamento(
    start_date: DateInput | None = None,
    end_date: DateInput | None = None,
    moeda_code: int | None = None,
    settings: BcbSettings | None = None,
) -> pd.DataFrame:
    """
    Fetch PTAX closing rates for a currency and date range.

    Returns columns: data, codigo, tipo, moeda, taxa_compra, taxa_venda,
    paridade_compra, paridade_venda.
    """
    cfg = settings or get_settings().bcb
    app = get_settings()
    code = moeda_code if moeda_code is not None else cfg.ptax_moeda_code

    end_dt = ensure_date(end_date) if end_date is not None else date.today()
    start_dt = ensure_date(start_date) if start_date is not None else app.data_start_date

    if start_dt > end_dt:
        raise ValueError("start_date cannot be after end_date.")

    # BCB returns HTML instead of CSV when DATAINI == DATAFIM; widen fetch then filter.
    fetch_start = start_dt
    if start_dt == end_dt:
        fetch_start = start_dt - timedelta(days=_SINGLE_DAY_LOOKBACK_DAYS)

    chunks = _split_period_in_year_chunks(fetch_start, end_dt)
    frames: list[pd.DataFrame] = []

    for chunk_start, chunk_end in chunks:
        url = build_ptax_fechamento_url(chunk_start, chunk_end, moeda_code=code, settings=cfg)
        try:
            text = _fetch_csv_text(url, cfg.timeout, cfg.max_retries)
        except Exception as ex:
            logger.warning("BCB PTAX: chunk failed %s to %s: %s", chunk_start, chunk_end, ex)
            raise

        df_chunk = _csv_text_to_dataframe(text)
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
    mask = (df_final["data"].dt.date >= start_dt) & (df_final["data"].dt.date <= end_dt)
    return df_final.loc[mask].reset_index(drop=True)


def fetch_ptax_usd(
    start_date: DateInput | None = None,
    end_date: DateInput | None = None,
    settings: BcbSettings | None = None,
) -> pd.DataFrame:
    """Fetch USD PTAX closing rates (ChkMoeda from settings, default 61)."""
    cfg = settings or get_settings().bcb
    return fetch_ptax_fechamento(
        start_date=start_date,
        end_date=end_date,
        moeda_code=cfg.ptax_moeda_code,
        settings=cfg,
    )
