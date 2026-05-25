"""Execute SQL queries and return pandas DataFrames."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.database.connection import get_connection

_QUERIES_DIR = Path(__file__).resolve().parent.parent / "queries"


def queries_dir() -> Path:
    return _QUERIES_DIR


def load_query(name: str) -> str:
    """Load ``queries/{name}.sql`` (without extension in ``name``)."""
    path = _QUERIES_DIR / f"{name}.sql"
    if not path.is_file():
        raise FileNotFoundError(f"SQL query not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def normalize_iso_date(value: str, *, param: str = "date") -> str:
    text = str(value).strip()[:10]
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        raise ValueError(f"Invalid ISO date for {param}: {value!r}")
    return text


def query_to_dataframe(
    sql: str,
    params: tuple[Any, ...] = (),
    *,
    db_path: Any = None,
) -> pd.DataFrame:
    conn = get_connection(db_path)
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([dict(r) for r in rows])
    finally:
        conn.close()
