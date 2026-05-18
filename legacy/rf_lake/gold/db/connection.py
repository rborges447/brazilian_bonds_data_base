"""
SQLite connection management.

Provides functions to create and manage SQLite database connections.
Configured for concurrent access (WAL mode).
"""
import sqlite3
from pathlib import Path
from typing import Optional, Union

from rf_lake.settings import DB_PATH


def get_conn(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """
    Create a new SQLite database connection.

    Settings applied:
    - Foreign keys enabled
    - WAL mode (Write-Ahead Logging) for concurrent readers
    - Synchronous NORMAL for better performance
    - 30 second timeout for lock operations

    Args:
        db_path: Optional path to the database file.
                 If omitted, uses the configured default path.
                 May be str or Path.

    Returns:
        Configured SQLite connection.

    Note:
        Close the connection explicitly or use a context manager.
        For automatic handling, use Database.transaction().
    """
    path = db_path or DB_PATH
    if isinstance(path, str):
        path = Path(path)
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create connection with lock timeout
    conn = sqlite3.connect(str(path), timeout=30)
    
    # Settings for concurrent access
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    
    return conn
