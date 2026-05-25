# Architecture — Current Project With Public read_data API

## Architectural Intent

This architecture document describes the incremental target architecture based on the current project structure.

The existing `src/app` package remains the internal implementation package.

A public package facade will be added so external projects can import the database package cleanly and read curated data through **`read_data()`**, which masks the internal `GoldReader`.

## Current Internal Structure

The current architecture is organized around:

```text
src/app/
  cli/
  config/
  contracts/
  core/
  database/
  lake/
    bronze/
    silver/
    gold/
  providers/
  repositories/
  services/
```

This structure should not be replaced during the first phase.

## Target External Usage

External projects should use:

```python
import brazilian_bonds_db as bbdb

bbdb.update()

data = bbdb.read_data()
df = data.cdi.fetch_all()
```

or:

```python
from brazilian_bonds_db import read_data

data = read_data()
df = data.ptax.fetch_range("2025-01-01", "2025-12-31")
```

External users must not be required to import or instantiate `GoldReader`.

## Target Incremental Structure

Add a thin public API layer without moving the current internals:

```text
src/
  app/
    cli/
    config/
    contracts/
    core/
    database/
    lake/
    providers/
    repositories/
    services/
    public/
      __init__.py
      update.py
      readers.py          # exposes read_data(); GoldReader stays internal

  brazilian_bonds_db/
    __init__.py
    update.py
    readers.py            # re-exports read_data from app.public
```

Optional compatibility module:

```text
src/brazilian_bonds_db/queries.py
```

If kept, `queries.py` should not become the primary public API. It may exist only as a compatibility shim or convenience wrapper.

## Role of `src/app`

`src/app` remains the internal implementation package.

It owns:

- providers
- bronze/silver/gold
- migrations
- database readers (including internal `GoldReader`)
- repositories
- services
- CLI
- internal configuration
- current pipeline logic

External users should not import these modules directly.

## Role of `src/app/public`

`src/app/public` is the internal public facade.

It defines stable user-facing operations on top of the current implementation.

Responsibilities:

- expose `update()`
- expose `read_data()` as the only public read entrypoint
- delegate read operations to internal `GoldReader` (or equivalent) without exposing that name to consumers
- delegate to current services/readers/repositories
- hide bronze/silver/gold internals
- hide migrations
- hide SQL file paths
- hide provider details

It should remain thin.

It should not contain provider logic, transformation logic, SQL logic, or migration implementation.

## Role of `src/brazilian_bonds_db`

`src/brazilian_bonds_db` is the import alias package.

Its job is to allow:

```python
import brazilian_bonds_db as bbdb
```

It should delegate to `app.public`.

Example:

```python
from app.public.update import update
from app.public.readers import read_data
```

This keeps the current architecture intact while exposing a clean package name.

## Dependency Direction

Allowed:

```text
brazilian_bonds_db -> app.public -> app.services / app.database / app.lake
```

Allowed temporarily:

```text
app.public -> app.database.readers.GoldReader   # internal only, behind read_data()
app.public -> app.services
app.public -> existing internal orchestration
```

Forbidden:

```text
app.lake -> brazilian_bonds_db
app.database -> brazilian_bonds_db
app.providers -> brazilian_bonds_db
app.core -> brazilian_bonds_db
```

Internal modules must not depend on the import alias.

## Public API Layer

Location:

```text
src/app/public/
```

and alias:

```text
src/brazilian_bonds_db/
```

Responsibilities:

- stable external API
- simple function signatures
- DataFrame-returning read operations through the object returned by `read_data()`
- update orchestration entrypoint

Public symbols (consumer-facing):

```python
update()
read_data()
```

Expected user experience:

```python
data = bbdb.read_data()

data.cdi.fetch_all()
data.cdi.fetch_latest(10)
data.cdi.fetch_on("2025-01-10")
data.cdi.fetch_range("2025-01-01", "2025-12-31")
```

## read_data Public Contract

`read_data()` returns a dataset-oriented accessor (implemented internally by `GoldReader`).

Expected available datasets should follow the current project implementation, for example:

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

Each dataset reader may expose methods according to the dataset type:

```python
fetch_all()
fetch_latest(n)
fetch_on(date)
fetch_range(start_date, end_date)
```

Not all datasets need all methods if the method does not make sense for that dataset.

## Services Layer

Location:

```text
src/app/services/
```

Responsibilities:

- coordinate higher-level workflows
- expose reusable internal operations
- support `app.public.update`
- keep CLI thin

Recommended additions:

```text
src/app/services/local_environment_service.py
src/app/services/update_database_service.py
src/app/services/migration_service.py
```

These services should wrap existing logic instead of rewriting it.

## Database Layer

Location:

```text
src/app/database/
```

Responsibilities:

- migrations
- SQL files
- readers (including `GoldReader` — internal)
- database initialization
- connection management
- schema control

The public API must not expose SQL file names, migration commands, or the `GoldReader` class name.

## Lake Layer

Location:

```text
src/app/lake/
```

Responsibilities:

- bronze ingestion
- silver normalization
- gold dataset construction

This layer remains internal.

External users should never call it directly.

## Providers Layer

Location:

```text
src/app/providers/
```

Responsibilities:

- access external data sources
- fetch source data
- return raw or minimally parsed data

Providers should remain internal.

## CLI Layer

Location:

```text
src/app/cli/
```

Responsibilities:

- command-line interface for development/operations
- parse CLI arguments
- delegate to services

The CLI should not be the only way to update the database.

The public Python API must work without CLI.

## Local Data Folder

Default target:

```text
./data/brazilian_bonds_db/
```

Suggested internal layout:

```text
data/
  brazilian_bonds_db/
    database/
    lake/
      bronze/
      silver/
      gold/
    logs/
    metadata/
```

## Migration Rule

Migrations must run automatically when needed.

The user should call:

```python
bbdb.update()
```

not:

```bash
python -m app.database.migrate
```

## Refactoring Rule

Do not move existing working internals unless a task explicitly requires it.

The first phase is facade-first:

```text
existing internals stay where they are
public API wraps them
read_data() is the user-facing read entrypoint
tests validate external usage
```
