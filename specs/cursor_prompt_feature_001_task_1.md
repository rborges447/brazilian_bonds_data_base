# Cursor Prompt — Start SDD Feature 001

Read these files first:

```text
specs/specs/000-project-foundation/project.md
specs/specs/000-project-foundation/architecture.md
specs/specs/001-public-database-api/spec.md
specs/specs/001-public-database-api/tasks.md
```

Implement only Task 1 from `001-public-database-api/tasks.md`.

Goal:

Create:

```text
src/app/public/__init__.py
src/app/public/update.py
src/app/public/readers.py
```

Requirements:

- keep the current architecture
- do not move existing modules
- do not modify bronze/silver/gold
- do not modify providers
- do not modify migrations
- do not break CLI
- importing `app.public` must not run I/O, migrations, providers, or pipelines
- expose names: `update`, `read_data` (not `read_gold` / not `GoldReader` on public surface)

Temporary `NotImplementedError` is acceptable for functions not wired yet.

Add minimal tests proving:

```python
from app.public import update, read_data
```

works.

After finishing:

1. list changed files
2. show tests run
3. stop
