"""Split and merge ANBIMA projections payloads by mes_referencia (bronze hive)."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from pipelines.bronze.incremental import missing_partition_values
from pipelines.bronze.paths import bronze_partition_path
from pipelines.bronze.writer import write_partition_json

_DEDUP_KEYS = ("indice", "tipo_projecao", "data_coleta", "mes_referencia")
_PARTITION_KEY = "reference_month"
_DATASET = "projecoes"


def flatten_projecoes_payload(payload: Any) -> list[dict]:
    """Turn API JSON (list, dict, or nested list) into a flat list of record dicts."""
    if payload is None:
        return []
    if isinstance(payload, dict):
        return [payload]
    if not isinstance(payload, list):
        return []
    records: list[dict] = []
    for item in payload:
        if isinstance(item, dict):
            records.append(item)
        elif isinstance(item, list):
            records.extend(x for x in item if isinstance(x, dict))
    return records


def mes_referencia_to_partition_key(mes_referencia: str) -> str:
    """Map mes_referencia (MM/YYYY, MM-YYYY, or ISO) to reference_month=YYYY-MM-01."""
    s = str(mes_referencia).strip()
    m = re.match(r"^(\d{1,2})[/-](\d{4})$", s)
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}-01"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s[:7] + "-01"
    if re.match(r"^\d{4}-\d{2}$", s):
        return f"{s}-01"
    raise ValueError(f"Invalid mes_referencia for partition key: {mes_referencia!r}")


def group_records_by_reference_month(records: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for record in records:
        raw = record.get("mes_referencia") or record.get("ref_month")
        if raw is None:
            continue
        key = mes_referencia_to_partition_key(str(raw))
        grouped.setdefault(key, []).append(record)
    return grouped


def _record_dedup_key(record: dict) -> tuple[str, ...]:
    return tuple(str(record.get(k, "")).strip() for k in _DEDUP_KEYS)


def merge_projecoes_records(existing: list[dict], new: list[dict]) -> list[dict]:
    """Append new coletas; dedupe identical (indice, tipo_projecao, data_coleta, mes_referencia)."""
    seen: set[tuple[str, ...]] = set()
    merged: list[dict] = []
    for record in existing + new:
        key = _record_dedup_key(record)
        if key in seen:
            continue
        seen.add(key)
        merged.append(record)
    merged.sort(key=lambda r: str(r.get("data_coleta", "")))
    return merged


def load_partition_records(partition_value: str) -> list[dict]:
    """Load raw projection records from a bronze JSON partition."""
    path = bronze_partition_path(_DATASET, _PARTITION_KEY, partition_value, "json")
    if not path.is_file() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8") as handle:
        return flatten_projecoes_payload(json.load(handle))


def write_merged_partition(partition_value: str, new_records: list[dict]) -> None:
    existing = load_partition_records(partition_value)
    merged = merge_projecoes_records(existing, new_records)
    write_partition_json(_DATASET, _PARTITION_KEY, partition_value, merged, "json")


def _active_calendar_month_keys() -> set[str]:
    """Current, previous, and next calendar month (covers mês posterior in API)."""
    today = date.today()

    def _shift(month: int, year: int, delta: int) -> tuple[int, int]:
        m = month + delta
        y = year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        return m, y

    keys: set[str] = set()
    for delta in (-1, 0, 1):
        m, y = _shift(today.month, today.year, delta)
        keys.add(f"{y:04d}-{m:02d}-01")
    return keys


def partitions_to_refresh_projecoes(candidate_months: list[str]) -> set[str]:
    """
    Months to (re)pull from API: missing bronze partitions plus active calendar months.
    """
    missing = set(missing_partition_values(_DATASET, candidate_months))
    return missing | _active_calendar_month_keys()


def partition_key_to_mes_ano(partition_value: str) -> tuple[int, int]:
    return int(partition_value[5:7]), int(partition_value[:4])
