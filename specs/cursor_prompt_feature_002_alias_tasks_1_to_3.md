# Cursor Prompt — Start SDD Feature 002

Only start this after `app.public` exposes `read_data`.

Read these files first:

```text
specs/specs/000-project-foundation/project.md
specs/specs/000-project-foundation/architecture.md
specs/specs/002-import-alias-brazilian-bonds-db/spec.md
specs/specs/002-import-alias-brazilian-bonds-db/tasks.md
```

Implement only Tasks 1, 2 and 3 from `002-import-alias-brazilian-bonds-db/tasks.md`.

Goal:

Create:

```text
src/brazilian_bonds_db/__init__.py
src/brazilian_bonds_db/update.py
src/brazilian_bonds_db/readers.py
```

Requirements:

- `import brazilian_bonds_db as bbdb` works
- `bbdb.update` exists
- `bbdb.read_data` exists and is callable
- delegate to `app.public`
- do not duplicate business logic
- do not move existing `src/app` modules
- no heavy import side effects
- do not expose `GoldReader` or `read_gold` as primary API on the alias package

Add minimal tests for the import alias.

After finishing:

1. list changed files
2. show tests run
3. stop
