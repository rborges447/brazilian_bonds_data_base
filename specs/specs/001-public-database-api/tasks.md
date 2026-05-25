# Tasks — 001 Public Database API

## Agent Rule

Execute one task at a time.

Do not implement the whole feature in one pass.

After each task:

1. show changed files
2. run relevant tests
3. explain what was preserved
4. stop

---

## Task 1 — Create `app.public` Package

### Goal

Create the public facade package inside the existing architecture.

### Files

```text
src/app/public/__init__.py
src/app/public/update.py
src/app/public/readers.py
```

### Requirements

- `from app.public import update` works
- `from app.public import read_data` works
- do not expose `GoldReader` or `read_gold` as primary public symbols
- no heavy import side effects
- no existing modules moved

### Initial Behavior

`update()` may raise `NotImplementedError` temporarily if the real update service is not connected yet.

`read_data()` may raise `NotImplementedError` temporarily, or delegate to internal `GoldReader` if safe.

If importing internal `GoldReader` at module level creates heavy side effects, use a lazy import inside `read_data()` and document it.

### Tests

Add a test that imports `app.public` and `read_data`.

---

## Task 2 — Connect Public `read_data()`

### Goal

Make `app.public.readers.read_data()` delegate to the existing internal `GoldReader`.

### Requirements

- expose `read_data()` only (not `read_gold` / not `GoldReader` on public surface)
- support optional database/data path argument if the current reader supports it
- do not duplicate existing reader logic
- do not expose SQL file paths

### Do Not

- rewrite the entire reader layer
- move existing database readers
- change database schema
- require consumers to import `GoldReader` by name

---

## Task 3 — Create Local Environment Service

### Goal

Add a service that resolves and creates the local data folder for package usage.

### Suggested File

```text
src/app/services/local_environment_service.py
```

### Default Data Root

```text
./data/brazilian_bonds_db/
```

### Requirements

- create directory if missing
- support optional custom root path
- keep behavior testable with `tmp_path`

---

## Task 4 — Create Migration Service

### Goal

Wrap current migration logic in a service callable from Python.

### Suggested File

```text
src/app/services/migration_service.py
```

### Requirements

- reuse current migration implementation
- run pending migrations idempotently
- no CLI required
- callable from `update()`

---

## Task 5 — Create Update Database Service

### Goal

Create a service that backs public `update()`.

### Suggested File

```text
src/app/services/update_database_service.py
```

### Responsibilities

- initialize local environment
- run migrations
- detect missing/stale data using existing logic where possible
- run required update flow
- return a structured report

### Do Not

- rewrite all lake logic
- move bronze/silver/gold
- remove CLI

---

## Task 6 — Wire `app.public.update.update()`

### Goal

Make public `update()` call the update database service.

### Requirements

- `update()` callable from Python
- no shell command required
- optional parameters may include:
  - `data_root`
  - `datasets`
  - `start_date`
  - `end_date`
  - `force`
- return structured report

---

## Task 7 — Add Integration Tests

### Goal

Test the public database API from the perspective of a package consumer.

### Tests

```text
tests/public/test_public_imports.py
tests/public/test_read_data_public_api.py
tests/public/test_update_creates_data_dir.py
```

### Requirements

- use temporary directory
- avoid external provider calls unless marked integration
- verify public API shape (`update`, `read_data`)
- verify `read_data()` returns an object with dataset attributes (e.g. `cdi`, `ptax`)
- do not require `GoldReader` in consumer-facing tests
