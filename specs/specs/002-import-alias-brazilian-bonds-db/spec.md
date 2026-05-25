# Feature Spec — Import Alias `brazilian_bonds_db`

## Feature Name

`002-import-alias-brazilian-bonds-db`

## Objective

Allow external users to import the project with a clean package name:

```python
import brazilian_bonds_db as bbdb
```

This feature must preserve the current internal architecture under `src/app`.

The alias package should delegate to `app.public`.

## Why This Exists

The current internal implementation package is named:

```text
app
```

That name is too generic for external package use.

The public package name should communicate the product clearly:

```text
brazilian_bonds_db
```

## Target Usage

```python
import brazilian_bonds_db as bbdb

bbdb.update()

data = bbdb.read_data()
df = data.cdi.fetch_latest(10)
```

Alternative usage:

```python
from brazilian_bonds_db import read_data

data = read_data()
df = data.mercado_secundario.fetch_range("2025-01-01", "2025-12-31")
```

## Required Structure

Add:

```text
src/brazilian_bonds_db/
  __init__.py
  update.py
  readers.py
```

Optional compatibility module:

```text
src/brazilian_bonds_db/queries.py
```

Only add `queries.py` if a compatibility shim is desired. It should not become the primary read API.

## Relationship With Existing Code

The alias package must not implement business logic.

It must delegate to:

```text
src/app/public/
```

Expected relationship:

```text
brazilian_bonds_db -> app.public -> existing app internals
```

## Functional Requirements

### FR-001 — Import package

This must work:

```python
import brazilian_bonds_db as bbdb
```

### FR-002 — Expose `update`

This must work:

```python
bbdb.update()
```

Implementation should delegate to:

```python
app.public.update.update
```

### FR-003 — Expose `read_data`

This must work:

```python
data = bbdb.read_data()
df = data.cdi.fetch_latest(10)
```

Implementation should delegate to:

```python
app.public.readers.read_data
```

### FR-004 — Do not expose `GoldReader` / `read_gold` as primary API

The alias package must not promote:

```python
bbdb.GoldReader
bbdb.read_gold()
```

Consumers interact with `read_data()` only.

Internal `GoldReader` remains an implementation detail behind `read_data()`.

### FR-005 — Support direct `read_data` import

This should work:

```python
from brazilian_bonds_db import read_data
from brazilian_bonds_db.readers import read_data
```

### FR-006 — No duplicated logic

Do not duplicate reader logic between:

```text
app.public.readers
brazilian_bonds_db.readers
```

`brazilian_bonds_db.readers` should re-export `read_data` from `app.public.readers`.

### FR-007 — No heavy import side effects

Importing `brazilian_bonds_db` must not:

- run update
- run migrations
- fetch provider data
- create files
- connect eagerly to database unless already safe in existing internals

## Packaging Requirements

Update package configuration if needed so `src/brazilian_bonds_db` is included when installing.

Check:

```text
pyproject.toml
```

The package must be discoverable in editable install:

```bash
pip install -e .
```

## Acceptance Criteria

- `import brazilian_bonds_db as bbdb` works.
- `bbdb.update` exists.
- `bbdb.read_data` exists.
- `bbdb.read_data()` returns a dataset accessor usable as `data.cdi.fetch_*`.
- `from brazilian_bonds_db import read_data` works.
- `from brazilian_bonds_db.readers import read_data` works.
- alias package does not contain business logic.
- `GoldReader` / `read_gold` are not listed as primary public symbols on the alias package.
- existing `app` imports continue to work.
- package discovery includes both `app` and `brazilian_bonds_db` if needed.
