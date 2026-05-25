"""Database connection and migrations."""

from app.database.connection import Dialect, commit, execute, execute_script, get_connection, get_dialect
from app.database.migrate import MIGRATIONS_DIR, apply_migrations
from app.database.readers import GoldReader
from app.database.schema import (
    BUSINESS_TABLES_V2,
    IPCA_DICT_COLUMNS,
    TABLE_CDI,
    TABLE_FERIADOS,
    TABLE_IPCA_DICT,
    TABLE_PTAX,
    validate_dataframe_columns,
)

__all__ = [
    "BUSINESS_TABLES_V2",
    "Dialect",
    "IPCA_DICT_COLUMNS",
    "MIGRATIONS_DIR",
    "TABLE_CDI",
    "TABLE_FERIADOS",
    "TABLE_IPCA_DICT",
    "TABLE_PTAX",
    "GoldReader",
    "apply_migrations",
    "commit",
    "execute",
    "execute_script",
    "get_connection",
    "get_dialect",
    "validate_dataframe_columns",
]