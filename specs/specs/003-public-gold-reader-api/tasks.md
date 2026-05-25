# Tasks — 003 Public read_data API (documentation & onboarding)

## Agent Rule

Execute one task at a time.

Do not rewrite reader internals unless the task explicitly requires it.

**Context:** Features `001-public-database-api` and `002-import-alias-brazilian-bonds-db` already implement `read_data()` / `update()` in code and tests. This feature focuses on **documentation**, **README for package consumers**, and **verification** — not a second API implementation.

See also: [`revision-proposal.md`](revision-proposal.md).

---

## Task 1 — Document `read_data` public API

### Goal

Inventory internal `GoldReader` and publish the **consumer-facing** contract for `read_data()`.

### Inspect (no code changes required)

- import path: `app.database.readers.gold_reader.GoldReader`
- delegation: `app.public.readers.read_data` → `GoldReader`
- constructor / factory parameters: `db_path`, `data_root` (via `ensure_local_environment`)
- dataset attributes and reading methods per dataset type

### Output

Create:

```text
docs/gold_reader_public_api.md
```

Requirements:

- Title the main consumer section **read_data public API** (not GoldReader as primary name)
- List only datasets that exist on `GoldReader` today (do not invent APIs)
- Document common methods: `fetch_all`, `fetch_latest`, `fetch_on`, `fetch_range` where applicable
- One line pointing to implementation: `src/app/public/readers.py`
- Optional: link to `tests/public/` for regression tests

### Do Not

- Change `GoldReader` implementation in this task unless a doc audit finds a critical mismatch (then stop and report)

---

## Task 2 — Verify `read_data()` in `app.public` (done in 001)

### Status

**Completed by Feature 001.** This task is a **verification checkpoint** only.

### Goal

Confirm:

```python
from app.public import read_data
```

### Checklist

- [ ] `src/app/public/readers.py` delegates to `GoldReader`
- [ ] `app.public.__all__` exposes `read_data` (not `GoldReader` / `read_gold`)
- [ ] `tests/public/test_read_data_public_api.py` passes
- [ ] Importing `app.public` does not run `update()` (see `test_import_app_public_does_not_run_update`)

### Do Not

- Reimplement `read_data()` or duplicate tests unless a regression is found

---

## Task 3 — Verify `read_data()` in `brazilian_bonds_db` (done in 002)

### Status

**Completed by Feature 002.** Verification checkpoint only.

### Goal

Confirm:

```python
import brazilian_bonds_db as bbdb
data = bbdb.read_data()
```

### Checklist

- [ ] `src/brazilian_bonds_db/readers.py` re-exports `app.public.readers.read_data`
- [ ] `brazilian_bonds_db.__all__` is `["read_data", "update"]`
- [ ] `tests/public/test_brazilian_bonds_db_alias.py` passes
- [ ] `pip install -e .` makes `brazilian_bonds_db` importable (`pyproject.toml` includes `brazilian_bonds_db*`)

### Do Not

- Add business logic to the alias package

---

## Task 4 — Verify public reader tests (done in 001/002)

### Status

**Completed by Features 001 and 002.** Verification checkpoint only.

### Goal

Confirm automated coverage of the consumer experience without requiring `GoldReader` in test assertions.

### Checklist

- [ ] `tests/public/test_read_data_public_api.py` exists and passes
- [ ] `tests/public/test_brazilian_bonds_db_alias.py` exists and passes
- [ ] `pytest tests/public/ -q` green after any doc/README changes in Tasks 1, 5, 6

### Reference tests (already implemented)

- `import brazilian_bonds_db as bbdb`
- `callable(bbdb.read_data)`
- `data = bbdb.read_data(...)` with `tmp_path` + `data.cdi.fetch_all()` where applicable

### Do Not

- Require `GoldReader` or `read_gold` in consumer-facing assertions

---

## Task 5 — README for package consumers

### Goal

Document end-to-end usage for someone installing the package from GitHub.

### Source

Use and refine: [`docs/README_PACKAGE_USER_DRAFT.md`](../../../docs/README_PACKAGE_USER_DRAFT.md).

### README must include

1. What the package is (`brazilian_bonds_db` — local DB, `update` + `read_data`)
2. Requirements (Python 3.10+)
3. Clone from GitHub → venv → `pip install -e .` (and optional `.[dev]`)
4. `.env` / credentials (ANBIMA, `DATA_START_DATE`, etc.) — link to `.env.example`
5. Default data layout: `./data/brazilian_bonds_db/`
6. `bbdb.update()` and `bbdb.read_data()` with examples and main parameters
7. Dataset overview (or link to `docs/gold_reader_public_api.md`)
8. Troubleshooting (import, empty DB, sync credentials)
9. Short pointer to contributor/CLI docs (Task 6)

### Do Not

- Present `GoldReader()`, `read_gold()`, or `queries.get_*()` as the **main** consumer API
- Remove maintainer documentation entirely — defer pipeline/CLI detail to Task 6

### Replace placeholder

- Set real GitHub clone URL (`SEU_ORG/SEU_REPO`) when known

---

## Task 6 — Split consumer README vs development docs

### Goal

Apply **option B** from [`revision-proposal.md`](revision-proposal.md):

- **`README.md`** — package consumer (Task 5 content, concise)
- **`docs/development.md`** — bronze/silver/gold CLI, `src/app/` layout, `run_sync.py`, internal `GoldReader` for contributors

### Requirements

- Move or adapt current README sections (pipeline por camada, `rf-analytics`, estrutura `src/app/`) into `docs/development.md`
- Link from README: “Desenvolvimento do repositório → [docs/development.md](../../docs/development.md)”
- Keep links to existing docs (`gold_schema_v2.md`, `project_architecture_and_dependencies.md`, etc.)

### Do Not

- Break existing script entrypoints or paths referenced by contributors

---

## Feature 003 — Acceptance checklist

After Tasks 1, 5, and 6 (and verification 2–4):

- [ ] `docs/gold_reader_public_api.md` exists; datasets match `GoldReader`
- [ ] README: GitHub → install → config → `update()` → `read_data()`
- [ ] README does not promote `GoldReader` as consumer API
- [ ] `docs/development.md` exists for maintainers
- [ ] `pytest tests/public/ -q` passes
- [ ] Code from 001/002 unchanged unless audit found a gap
