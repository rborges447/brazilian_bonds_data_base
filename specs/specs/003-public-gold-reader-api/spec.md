# Feature Spec — Public read_data API (mask over GoldReader)

## Feature Name

`003-public-gold-reader-api`

> **Note:** Feature id kept for traceability. The public read contract is **`read_data()`**, not `read_gold()` / `GoldReader`.

## Status and dependencies

- **Prerequisites (completed):** `001-public-database-api`, `002-import-alias-brazilian-bonds-db`
- **Scope of this feature:** document the `read_data()` contract, verify parity with internal `GoldReader`, update README for package consumers (install from GitHub through daily use)
- **Out of scope:** reimplement `read_data()`, new import alias, lake/CLI changes (except contributor documentation)

Implementation already lives in:

```text
app.public.readers.read_data  →  GoldReader
brazilian_bonds_db.read_data  →  app.public.readers.read_data
```

## Objective

Formalize and document the **public read contract** `read_data()` for package consumers.

This feature delivers:

1. Consumer-facing API reference (`docs/gold_reader_public_api.md`)
2. End-to-end README (GitHub clone → `pip install -e .` → credentials → `update()` → `read_data()` → datasets)
3. Verification that documented datasets and methods match `GoldReader` (no invented APIs)

Users interact with `read_data()` only; they must not need the internal class name `GoldReader`.

## Target Usage

```python
import brazilian_bonds_db as bbdb

bbdb.update()

data = bbdb.read_data()

df = data.cdi.fetch_latest(10)
df = data.ptax.fetch_range("2025-01-01", "2025-12-31")
df = data.titulos_publicos.fetch_all()
```

Alternative usage:

```python
from brazilian_bonds_db import read_data

data = read_data()
df = data.mercado_com_liquidacoes.fetch_on("2026-01-10")
```

## Design Decision

The package should not primarily expose many top-level query functions.

Preferred:

```python
data = bbdb.read_data()
data.cdi.fetch_all()
```

Avoid as the main API:

```python
queries.get_cdi()
from brazilian_bonds_db import GoldReader
bbdb.read_gold()
```

Reason:

- `read_data()` is a single discoverable entrypoint
- the returned object groups curated datasets (same ergonomics as internal `GoldReader`)
- dataset readers can expose different reading styles
- the interface is easy to explore in IDE autocomplete
- internal `GoldReader` can stay unchanged; only the public name changes

## Functional Requirements

### FR-001 — Public `read_data()`

The package must expose:

```python
from brazilian_bonds_db import read_data
```

and:

```python
import brazilian_bonds_db as bbdb
data = bbdb.read_data()
```

### FR-002 — Mask internal `GoldReader`

`read_data()` must return an object with the same dataset-oriented API as internal `GoldReader`.

Implementation may be a direct factory:

```python
def read_data(db_path=None, data_root=None, **kwargs):
    from app.database.readers import GoldReader
    return GoldReader(db_path=...)
```

Do not require consumers to import `GoldReader`.

### FR-003 — Dataset Reader Access

The object returned by `read_data()` should expose dataset attributes already supported by internal `GoldReader`.

Expected examples:

```python
data.cdi
data.ptax
data.ipca_dict
data.titulos_publicos
data.mercado_secundario
data.liquidacoes_mercado
data.leiloes
data.ajustes_bmf
data.contratos_bmf
data.feriados
data.mercado_com_liquidacoes
```

The exact list should follow the real current `GoldReader` implementation.

Do not invent datasets that do not exist.

### FR-004 — Reading Methods

Dataset readers may expose different methods depending on the dataset.

Common methods:

```python
fetch_all()
fetch_latest(n)
fetch_on(date)
fetch_range(start_date, end_date)
```

Not every dataset must implement every method.

### FR-005 — Optional Paths

If internal `GoldReader` supports a custom database path, preserve that through `read_data()` parameters.

Possible usage:

```python
data = bbdb.read_data(data_root="./data/brazilian_bonds_db")
```

or:

```python
data = read_data(db_path="...")
```

### FR-006 — No SQL Exposure

Users must not need to know SQL file names or paths.

### FR-007 — No Lake Exposure

Users must not need to import gold builders, silver transforms, bronze extractors, or provider modules.

### FR-008 — Internal `GoldReader` unchanged for app code

Existing internal usage remains valid:

```python
from app.database import GoldReader  # internal / tests / notebooks
```

Package consumers use `read_data()` instead.

## Non-Functional Requirements

### NFR-001 — Thin Wrapper

Do not rewrite internal `GoldReader` unless necessary.

Implement `read_data()` as a thin factory in `app.public.readers` and re-export through `brazilian_bonds_db`.

### NFR-002 — IDE Discoverability

The public API should be easy to discover:

```python
bbdb.read_data
data.cdi
data.ptax
```

### NFR-003 — Backward Compatibility

Existing internal imports and `tests/database/test_gold_reader.py` should continue working.

## Acceptance Criteria

### Already satisfied (001 / 002 — verify in Tasks 2–4)

- `from brazilian_bonds_db import read_data` works.
- `bbdb.read_data()` works.
- `read_data()` returns an object with dataset attributes matching internal `GoldReader`.
- At least one dataset reader works from the public object without importing `app.database` or `app.lake`.
- `tests/public/` covers imports and basic `read_data()` usage.

### Delivered by this feature (Tasks 1, 5, 6)

- `docs/gold_reader_public_api.md` exists and lists real datasets (no invented APIs).
- README describes: GitHub → venv → `pip install -e .` → `.env` → `update()` → `read_data()`.
- README does **not** present `GoldReader` as the primary consumer API.
- Maintainer pipeline/CLI documented in `docs/development.md` (linked from README).
- `pytest tests/public/ -q` remains green after documentation changes.

### Still required for consumers

- Public usage does not require `read_gold()` or `bbdb.GoldReader`.
- `GoldReader` may appear only as an implementation note for contributors.
