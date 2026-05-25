# Feature Spec — Public Database API Over Existing Project

## Feature Name

`001-public-database-api`

## Objective

Create a clean public API inside the existing architecture that exposes the project as a local database package.

This feature must not reorganize the full project.

It adds a facade over the existing implementation.

## Current Context

The project already contains working internal components under:

```text
src/app/
```

Important existing areas:

```text
src/app/database/
src/app/lake/
src/app/providers/
src/app/repositories/
src/app/services/
src/app/cli/
```

This feature must reuse those modules.

## Target Internal Public API

Create:

```text
src/app/public/
  __init__.py
  update.py
  readers.py
```

Expected internal usage (facade for external consumers via alias later):

```python
from app.public import update, read_data

update()

data = read_data()
df = data.cdi.fetch_all()
```

## Functional Requirements

### FR-001 — Create `app.public`

Add a new package:

```text
src/app/public/
```

This package is the stable facade over the current implementation.

### FR-002 — Expose `update()`

`app.public.update.update()` must exist.

It should delegate to existing update/sync/migration logic.

Initial implementation may wrap current CLI/service/orchestration logic, but must not require shell commands.

### FR-003 — Expose `read_data()`

`app.public` must expose `read_data()` as the **only** public read entrypoint.

`read_data()` is a mask over the existing internal `GoldReader` (or a thin wrapper). Consumers must not need to import or name `GoldReader`.

Expected import:

```python
from app.public import read_data
```

### FR-004 — Hide `GoldReader` from public surface

Do not expose `GoldReader` or `read_gold()` on `app.public.__all__` or primary documentation.

Internal code may still use `app.database.readers.GoldReader`. The facade implements:

```python
def read_data(...):
    from app.database.readers import GoldReader
    return GoldReader(...)
```

(or equivalent delegation without re-exporting the class name to consumers).

### FR-005 — Hide SQL details

The user must not need to know SQL file paths.

SQL details remain inside existing database readers/repositories.

### FR-006 — Hide lake details

The user must not need to import bronze/silver/gold modules to read data.

### FR-007 — Preserve CLI

Existing CLI behavior must remain working.

This feature adds Python API usage; it does not remove CLI usage.

### FR-008 — No heavy import side effects

Importing `app.public` must not:

- run migrations
- call providers
- read/write files
- create database connections unless lazy and safe

## Public Reader Contract

Preferred usage:

```python
data = read_data()

data.cdi.fetch_all()
data.cdi.fetch_latest(10)
data.cdi.fetch_on("2025-01-10")
data.cdi.fetch_range("2025-01-01", "2025-12-31")
```

The object returned by `read_data()` must preserve the current dataset-oriented behavior of internal `GoldReader`.

Do not replace it with many top-level query functions unless a compatibility layer is explicitly needed.

## Non-Functional Requirements

### NFR-001 — Minimal impact

Do not move existing modules in this feature.

### NFR-002 — Thin facade

`app.public` should delegate to existing services/readers/repositories.

### NFR-003 — Testable API

Add tests proving that:

```python
from app.public import update, read_data
```

works and that `read_data()` returns an object with expected dataset attributes.

### NFR-004 — Backward compatibility

Existing tests and internal imports (`from app.database import GoldReader`) should continue passing.

## Acceptance Criteria

- `from app.public import update` works.
- `from app.public import read_data` works.
- `read_data()` returns a dataset accessor with the same behavior as internal `GoldReader`.
- `GoldReader` is not required in public import examples or acceptance tests for package consumers.
- importing `app.public` does not run pipelines.
- existing CLI is not broken.
- tests cover public `read_data()` availability.
