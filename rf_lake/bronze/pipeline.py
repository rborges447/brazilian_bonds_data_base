"""Bronze pipeline: extração → data/raw (somente datas faltantes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from rf_lake.bronze.extract import (
    extract_ajustes_bmf,
    extract_feriados,
    extract_ipca_indice,
    extract_leiloes,
    extract_liquidacoes_mercado,
    extract_mercado_secundario,
    extract_projecoes,
)
from rf_lake.bronze.sources import AnbimaClient
from rf_lake.datasets import DatasetTask
from rf_lake.gold.db import get_conn
from rf_lake.gold.db.repositories import ProjecoesRepo
from rf_lake.incremental import bronze_artifact_path, missing_dates_bronze, snapshot_key_dates
from rf_lake.logging import get_logger
from rf_lake.watermarks import set_watermark

logger = get_logger(__name__)

BACKFILL_MONTHS = 60


@dataclass
class BronzeResult:
    name: str
    status: str  # success | skipped | error
    path: Path | None = None
    raw_rows: int = 0
    dates: list[str] = field(default_factory=list)
    dates_candidate: list[str] = field(default_factory=list)
    dates_processed: list[str] = field(default_factory=list)
    error: str | None = None


def _mes_ano_n_meses_atras(mes: int, ano: int, n: int) -> tuple[int, int]:
    m, a = mes, ano
    for _ in range(n):
        m -= 1
        if m < 1:
            m = 12
            a -= 1
    return m, a


def _projecoes_payloads() -> tuple[list[Any], list[str]]:
    today = date.today()
    current_m, current_y = today.month, today.year
    dates_key: list[str] = [today.isoformat()]

    conn_check = get_conn()
    try:
        backfill = not ProjecoesRepo.has_any(conn_check)
    finally:
        conn_check.close()

    client = AnbimaClient()
    payloads: list[Any] = []

    if backfill:
        start_m, start_y = _mes_ano_n_meses_atras(current_m, current_y, BACKFILL_MONTHS - 1)
        logger.info(
            "Projeções bronze: backfill %s meses (%s/%s .. %s/%s).",
            BACKFILL_MONTHS,
            start_m,
            start_y,
            current_m,
            current_y,
        )
        historico = client.fetch_projecoes_historico(
            start_mes=start_m,
            start_ano=start_y,
            end_mes=current_m,
            end_ano=current_y,
        )
        for resp in historico:
            payloads.append(resp if isinstance(resp, list) else [resp])
    else:
        prev_m = current_m - 1 if current_m > 1 else 12
        prev_y = current_y if current_m > 1 else current_y - 1
        for mes, ano in [(current_m, current_y), (prev_m, prev_y)]:
            resp = client.fetch_projecoes(mes, ano)
            if resp is not None:
                payloads.append(resp if isinstance(resp, list) else [resp])

    return payloads, dates_key


def _extract_projecoes_bronze(dates_to_run: list[str]) -> tuple[Path | None, int, list[str]]:
    payloads, dates_key = _projecoes_payloads()
    if not payloads:
        return None, 0, []
    return extract_projecoes(dates_key, payloads)


_EXTRACTORS = {
    "mercado_secundario": extract_mercado_secundario,
    "liquidacoes_mercado": extract_liquidacoes_mercado,
    "ajustes_bmf": extract_ajustes_bmf,
    "leiloes": extract_leiloes,
    "ipca_indice": extract_ipca_indice,
    "feriados": extract_feriados,
}


def run_bronze(name: str, candidate_dates: list[str]) -> BronzeResult:
    dates_candidate = list(candidate_dates)
    dates_to_run = missing_dates_bronze(name, candidate_dates)
    key = snapshot_key_dates(candidate_dates)

    if not dates_to_run:
        path = bronze_artifact_path(name, key)
        logger.info(
            "[%s] Bronze skipped: %s candidatas, 0 faltantes (raw já cobre)",
            name,
            len(dates_candidate),
        )
        return BronzeResult(
            name=name,
            status="skipped",
            path=path if path.is_file() else None,
            raw_rows=0,
            dates=key if path.is_file() else [],
            dates_candidate=dates_candidate,
            dates_processed=[],
        )

    try:
        if name == "projecoes":
            path, raw_rows, dates_processed = _extract_projecoes_bronze(dates_to_run)
        else:
            fn = _EXTRACTORS.get(name)
            if fn is None:
                raise ValueError(f"Dataset sem extrator bronze: {name}")
            path, raw_rows, dates_processed = fn(dates_to_run)

        if raw_rows > 0 and dates_processed:
            set_watermark(name, "bronze", dates_processed)

        logger.info(
            "[%s] Bronze: %s candidatas, %s com dados, %s linhas → %s",
            name,
            len(dates_candidate),
            len(dates_processed),
            raw_rows,
            path,
        )
        return BronzeResult(
            name=name,
            status="success",
            path=path,
            raw_rows=raw_rows,
            dates=dates_processed,
            dates_candidate=dates_candidate,
            dates_processed=dates_processed,
        )
    except Exception as exc:
        logger.error("[%s] Bronze error: %s", name, exc, exc_info=True)
        return BronzeResult(
            name=name,
            status="error",
            dates_candidate=dates_candidate,
            error=str(exc),
        )


def run_bronze_phase(tasks: list[DatasetTask]) -> dict[str, BronzeResult]:
    logger.info("=== Bronze phase (%s datasets) ===", len(tasks))
    results: dict[str, BronzeResult] = {}
    for task in tasks:
        results[task.name] = run_bronze(task.name, task.dates)
    logger.info("=== Bronze phase concluída ===")
    return results
