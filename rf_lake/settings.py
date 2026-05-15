"""Central configuration for rf_lake (Bronze / Silver / Gold)."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)

DATA_ROOT = PROJECT_ROOT / "data"
BRONZE_ROOT = DATA_ROOT / "raw"
SILVER_ROOT = DATA_ROOT / "silver"

_db_env = os.getenv("SQLITE_DB_PATH", "").strip()
if _db_env:
    _db_path = Path(_db_env)
    DB_PATH = _db_path if _db_path.is_absolute() else PROJECT_ROOT / _db_path
else:
    DB_PATH = DATA_ROOT / "app.db"

MIGRATIONS_DIR = Path(__file__).resolve().parent / "gold" / "db" / "migrations"


def _validate_iso_date(value: str, name: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} is invalid (expected YYYY-MM-DD): {value!r}") from exc
    return value


DATA_START_DATE = _validate_iso_date(
    os.getenv("DATA_START_DATE", "2026-01-01").strip(),
    "DATA_START_DATE",
)

ANBIMA_CLIENT_ID = os.getenv("ANBIMA_CLIENT_ID", "").strip()
ANBIMA_CLIENT_SECRET = os.getenv("ANBIMA_CLIENT_SECRET", "").strip()
ANBIMA_TIMEOUT = int(os.getenv("ANBIMA_TIMEOUT", "30"))
ANBIMA_MAX_RETRIES = int(os.getenv("ANBIMA_MAX_RETRIES", "3"))

BCB_TIMEOUT = int(os.getenv("BCB_TIMEOUT", "30"))
BCB_MAX_RETRIES = int(os.getenv("BCB_MAX_RETRIES", "3"))

TESOURO_TIMEOUT = int(os.getenv("TESOURO_TIMEOUT", "30"))
TESOURO_MAX_RETRIES = int(os.getenv("TESOURO_MAX_RETRIES", "3"))

UPTODATA_PASTA_INTEREST_RATE_BASE = os.getenv("UPTODATA_PASTA_INTEREST_RATE_BASE", "")
UPTODATA_ARQUIVO_INTEREST_RATE_BASE = os.getenv("UPTODATA_ARQUIVO_INTEREST_RATE_BASE", "")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip()


META_DIR = DATA_ROOT / "meta"


def ensure_data_layout() -> None:
    """Create data directories (raw, silver, meta, SQLite parent folder)."""
    for path in (DATA_ROOT, BRONZE_ROOT, SILVER_ROOT, META_DIR, DB_PATH.parent):
        path.mkdir(parents=True, exist_ok=True)
