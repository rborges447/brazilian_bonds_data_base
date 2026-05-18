"""
SQLite database module: persistence and reads.

This module contains all database infrastructure:
- SQLite connections (WAL mode, foreign keys)
- Versioned migration system
- Repositories (CRUD per table)
- Read queries (get_*)
- Schema and metadata

Responsibilities:
- Manage SQLite connections
- Run schema migrations
- Provide persistence interfaces (repositories) and read interfaces (queries)
- Maintain schema metadata (columns, types, rename maps)

Allowed dependencies:
- settings (for DB_PATH, MIGRATIONS_DIR)
- logging (for logs)
- Standard library and third-party libs (sqlite3, pandas, pathlib)

Forbidden dependencies:
- sources/ (must not depend on external sources)
- etl/ (must not depend on pipelines)
- jobs/ (must not depend on orchestration)
- export/ (must not depend on export)
- data_reader/ (must not depend on product data reader)
"""

from rf_lake.gold.db import schema
from rf_lake.gold.db.connection import get_conn
from rf_lake.gold.db.migrate import apply_migrations

__all__ = ["apply_migrations", "get_conn", "schema"]
