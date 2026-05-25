# Cursor Prompt — Start SDD Feature 003

Read these files first:

```text
specs/specs/000-project-foundation/project.md
specs/specs/000-project-foundation/architecture.md
specs/specs/003-public-gold-reader-api/spec.md
specs/specs/003-public-gold-reader-api/tasks.md
```

Implement only Task 1 from `003-public-gold-reader-api/tasks.md`.

Goal:

Locate the current internal `GoldReader` implementation and document how **`read_data()`** will mask it:

- internal import path (`GoldReader`)
- constructor signature
- available dataset attributes on the object returned by `read_data()`
- available reading methods per dataset
- whether construction performs DB/file I/O
- public factory signature for `read_data()`

Create or update:

```text
docs/gold_reader_public_api.md
```

Consumer-facing sections must use `read_data`, not `read_gold` / `GoldReader`.

Do not refactor code in this task.

After finishing:

1. list inspected files
2. list changed files
3. stop
