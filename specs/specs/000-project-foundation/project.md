# Project Foundation — Brazilian Bonds Local Database

## Objective

This project is a Python package whose purpose is to maintain and expose a local Brazilian financial database.

The project must remain focused on being a database package.

It is not currently intended to be:

- an API server
- a dashboard
- a full data platform
- an orchestration framework
- a pricing application

The final user should be able to install the project in any Python environment and use it from another project.

Target usage:

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

## Product Scope

The package must provide two main public capabilities:

1. `update()`
2. `read_data()` for reading curated datasets

The package must internally handle:

- local data folder creation
- database initialization
- migrations
- missing-date detection
- provider collection
- bronze/silver/gold processing
- persistence
- read access through `read_data()` (backed internally by the existing `GoldReader`)

## Current Architecture Constraint

The current project already has a working architecture under:

```text
src/app/
```

This refactor must not replace the whole architecture at once.

The first goal is to add a clean public API on top of the existing implementation.

Existing modules such as:

```text
src/app/lake/
src/app/providers/
src/app/database/
src/app/repositories/
src/app/services/
src/app/cli/
```

must be reused.

## Public API Goal

The external user should not need to know about:

- bronze
- silver
- providers
- migrations
- SQL files
- repositories
- internal paths
- CLI commands
- `GoldReader` (internal class name)

The user should only need:

```python
import brazilian_bonds_db as bbdb

bbdb.update()

data = bbdb.read_data()
df = data.cdi.fetch_all()
```

## read_data Philosophy

The public read API is **`read_data()`**: a stable entrypoint that masks the internal `GoldReader`.

The user interacts only with the object returned by `read_data()`. That object is object-oriented and dataset-oriented.

Instead of exposing many top-level query functions such as:

```python
bbdb.queries.get_cdi()
bbdb.queries.get_ptax()
```

or exposing the internal reader class directly:

```python
from app.database import GoldReader  # internal — not for package consumers
```

the preferred interface is:

```python
data = bbdb.read_data()

data.cdi.fetch_all()
data.cdi.fetch_latest(5)
data.cdi.fetch_range("2024-01-01", "2024-12-31")
data.ptax.fetch_on("2025-01-10")
data.titulos_publicos.fetch_all()
```

Implementation detail: `read_data()` may delegate to the existing `GoldReader` in `app.database`. Consumers must not depend on the `GoldReader` name.

## Data Location

When called from another project, the package should create and use a local data folder under the consumer project.

Default target:

```text
./data/brazilian_bonds_db/
```

This folder should contain the database, internal lake files, logs, and metadata needed by the package.

## Refactoring Principle

Do not redesign the full project now.

The refactor must be incremental:

1. preserve existing behavior
2. add a public package facade
3. wrap existing update/sync/migration logic
4. expose `read_data()` as the public read/query entrypoint (mask over internal `GoldReader`)
5. add import alias as `brazilian_bonds_db`
6. only then consider deeper folder restructuring

## Success Criteria

The project succeeds when another Python project can install it and run:

```python
import brazilian_bonds_db as bbdb

bbdb.update()

data = bbdb.read_data()
df = data.cdi.fetch_latest(10)
```

without directly importing `src/app/lake`, `src/app/database`, `src/app/providers`, using `GoldReader` by name, or using the CLI.
