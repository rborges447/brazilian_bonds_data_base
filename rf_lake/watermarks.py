"""Per-dataset watermarks: last business date with a non-empty artifact per layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rf_lake.datasets import DATASETS
from rf_lake.date_fields import date_candidates_for_layer
from rf_lake.incremental import dates_present_in_dir, is_snapshot_dataset
from rf_lake.settings import BRONZE_ROOT, DATA_ROOT, SILVER_ROOT

META_DIR = DATA_ROOT / "meta"
WATERMARKS_PATH = META_DIR / "dataset_watermarks.json"

Layer = str  # "bronze" | "silver"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_all() -> dict[str, Any]:
    if not WATERMARKS_PATH.is_file():
        return {}
    with WATERMARKS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _save_all(data: dict[str, Any]) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    with WATERMARKS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_watermark(dataset: str, layer: Layer = "bronze") -> str | None:
    data = _load_all()
    entry = data.get(dataset, {}).get(layer)
    if not entry:
        return None
    return entry.get("last_date")


def set_watermark(dataset: str, layer: Layer, dates_present: list[str]) -> None:
    """Update watermark using business dates only (ignores snapshot-only without last_date)."""
    if not dates_present:
        return

    if is_snapshot_dataset(dataset):
        last_date = max(dates_present) if dates_present != ["snapshot"] else None
    else:
        business = [d for d in dates_present if d != "snapshot"]
        if not business:
            return
        last_date = max(business)

    data = _load_all()
    ds_entry = data.setdefault(dataset, {})
    ds_entry[layer] = {
        "last_date": last_date,
        "updated_at": _utc_now_iso(),
    }
    _save_all(data)


def get_all_watermarks() -> dict[str, dict[str, str | None]]:
    """Return {dataset: {bronze: last_date, silver: last_date}}."""
    raw = _load_all()
    out: dict[str, dict[str, str | None]] = {}
    for dataset in DATASETS:
        entry = raw.get(dataset, {})
        out[dataset] = {
            "bronze": entry.get("bronze", {}).get("last_date"),
            "silver": entry.get("silver", {}).get("last_date"),
        }
    return out


def rebuild_watermarks_from_disk() -> dict[str, dict[str, str | None]]:
    """Rebuild watermarks by scanning existing Parquet files."""
    data: dict[str, Any] = {}

    for dataset in DATASETS:
        ds_entry: dict[str, Any] = {}

        if is_snapshot_dataset(dataset):
            for layer, root in (("bronze", BRONZE_ROOT), ("silver", SILVER_ROOT)):
                layer_dir = root / dataset
                if layer_dir.is_dir() and any(layer_dir.iterdir()):
                    ds_entry[layer] = {
                        "last_date": None,
                        "updated_at": _utc_now_iso(),
                    }
        else:
            for layer, root in (("bronze", BRONZE_ROOT), ("silver", SILVER_ROOT)):
                layer_dir = root / dataset
                candidates = date_candidates_for_layer(dataset, layer)
                present = dates_present_in_dir(layer_dir, candidates)
                business = sorted(d for d in present if d != "snapshot")
                if business:
                    ds_entry[layer] = {
                        "last_date": business[-1],
                        "updated_at": _utc_now_iso(),
                    }

        if ds_entry:
            data[dataset] = ds_entry

    _save_all(data)
    return get_all_watermarks()
