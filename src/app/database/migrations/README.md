# Gold SQL migrations v2 (canonical)

Greenfield schema aligned with `app.lake.gold` materializers.

- No `IPCA_INDICE` or `PROJECOES` at gold layer (silver Parquet only).
- Daily `CDI`, `PTAX`, `IPCA_DICT`.
- DDL avoids `WITHOUT ROWID` for future PostgreSQL portability.

Apply (default):

```python
from app.database import apply_migrations
apply_migrations()
```

Apply on a fresh `data/app.db` when upgrading from an older schema.
