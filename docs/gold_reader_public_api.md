# read_data public API

Consumer-facing reference for reading curated gold tables from the local SQLite database.

**Public entrypoints** (use these in application code):

```python
import brazilian_bonds_db as bbdb

data = bbdb.read_data()
```

```python
from brazilian_bonds_db import read_data
from brazilian_bonds_db.readers import read_data  # same function

data = read_data()
```

**Implementation:** `read_data()` in [`src/app/public/readers.py`](../src/app/public/readers.py) builds an internal `GoldReader` ([`src/app/database/readers/gold_reader.py`](../src/app/database/readers/gold_reader.py)). Package consumers must not import `GoldReader` by name.

**Tests:** [`tests/public/`](../tests/public/) (`test_read_data_public_api.py`, `test_brazilian_bonds_db_alias.py`).

**Schema detail:** table columns and DDL — [`gold_schema_v2.md`](gold_schema_v2.md).

---

## `read_data()` parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `db_path` | `str \| Path \| None` | SQLite file with gold tables. If omitted, uses project settings default (`SQLITE_DB_PATH` / dev layout). |
| `data_root` | `str \| Path \| None` | Package layout root. Creates `./data/brazilian_bonds_db/` (or custom path) and resolves `database/app.db`. Ignored when `db_path` is set. |

Rules:

- Unknown keyword arguments raise `TypeError`.
- `data_root` and `db_path`: when both could apply, explicit `db_path` wins; if only `data_root` is given, the environment service ensures directories and uses `database/app.db` under that root.
- Return value: dataset accessor with attributes documented below (same object shape as internal `GoldReader`).

Example:

```python
import brazilian_bonds_db as bbdb

data = bbdb.read_data(data_root="./data/brazilian_bonds_db")
# or
data = bbdb.read_data(db_path="/path/to/app.db")
```

Populate data first with `bbdb.update()` (see package README).

---

## Returned object: dataset attributes

Access curated data via attributes on the object returned by `read_data()`:

```python
data = bbdb.read_data()
df = data.cdi.fetch_latest(10)
```

All methods return **pandas** `DataFrame` instances.

### Daily series (date-partitioned tables)

Attributes: `cdi`, `ptax`, `ipca_dict`, `mercado_secundario`, `liquidacoes_mercado`, `leiloes`, `ajustes_bmf`, `vna`.

| Method | Description |
|--------|-------------|
| `fetch_all()` | Full table |
| `fetch_latest(n)` | All rows for the last `n` **distinct** reference dates (`n >= 1`); row count may exceed `n` on multi-row tables |
| `fetch_on(date)` | Single day, `date` as `YYYY-MM-DD` |
| `fetch_range(start, end)` | Inclusive range; `start` must be `<= end` |

Example:

```python
data.cdi.fetch_all()
data.ptax.fetch_latest(5)
data.ipca_dict.fetch_on("2026-01-15")
data.mercado_secundario.fetch_range("2026-01-01", "2026-03-31")
data.vna.fetch_on("2026-05-20")
```

### Snapshot tables (`fetch_all` only)

Attributes: `feriados`, `titulos_publicos`, `contratos_bmf`.

| Method | Description |
|--------|-------------|
| `fetch_all()` | Full snapshot |
| `fetch_latest(n)` | **Not supported** — raises `TypeError` |
| `fetch_on(date)` | **Not supported** — raises `TypeError` |
| `fetch_range(start, end)` | **Not supported** — raises `TypeError` |

Example:

```python
data.feriados.fetch_all()
data.titulos_publicos.fetch_all()
data.contratos_bmf.fetch_all()
```

### Combined mercado + liquidações (full outer)

Attributes:

- `mercado_com_liquidacoes` — primary name
- `mercado_liquidacoes` — alias to the same reader

| Method | Description |
|--------|-------------|
| `fetch_all()` | Full combined view |
| `fetch_latest(n)` | All combined rows for the last `n` distinct reference dates (union of mercado + liquidações dates) |
| `fetch_on(date)` | Single reference date |
| `fetch_range(start, end)` | Inclusive date range |

Example:

```python
data.mercado_com_liquidacoes.fetch_on("2026-01-10")
data.mercado_liquidacoes.fetch_range("2026-01-01", "2026-01-31")
```

---

## Quick reference table

| Attribute | Reader kind | `fetch_all` | `fetch_latest` | `fetch_on` | `fetch_range` |
|-----------|-------------|-------------|----------------|------------|---------------|
| `cdi` | Date series | yes | yes | yes | yes |
| `ptax` | Date series | yes | yes | yes | yes |
| `ipca_dict` | Date series | yes | yes | yes | yes |
| `mercado_secundario` | Date series | yes | yes | yes | yes |
| `liquidacoes_mercado` | Date series | yes | yes | yes | yes |
| `leiloes` | Date series | yes | yes | yes | yes |
| `ajustes_bmf` | Date series | yes | yes | yes | yes |
| `vna` | Date series | yes | yes | yes | yes |
| `feriados` | Snapshot | yes | no | no | no |
| `titulos_publicos` | Snapshot | yes | no | no | no |
| `contratos_bmf` | Snapshot | yes | no | no | no |
| `mercado_com_liquidacoes` | Combined | yes | yes | yes | yes |
| `mercado_liquidacoes` | Combined (alias) | yes | yes | yes | yes |

---

## What is not part of the public API

Do not rely on these as a package consumer:

- `from app.database import GoldReader` (internal / notebooks / repo tests)
- `bbdb.GoldReader`, `bbdb.read_gold()`
- SQL file paths under `src/app/database/queries/`
- Bronze, silver, gold pipeline modules under `app.lake`

---

## Internal reference (contributors)

| Item | Location |
|------|----------|
| `read_data` factory | `app.public.readers.read_data` |
| `GoldReader` facade | `app.database.readers.gold_reader.GoldReader` |
| Date series reader | `app.database.readers._date_series.DateSeriesTableReader` |
| Dimension readers | `app.database.readers._static` |
| Combined reader | `app.database.readers._mercado_liquidacoes.MercadoLiquidacoesReader` |
| Query execution | `app.database.readers._execute` |

Repo development (CLI sync, dev `data/app.db` layout): see [`development.md`](development.md) when available, or current [`README.md`](../README.md).
