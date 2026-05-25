# Tasks — 002 Import Alias `brazilian_bonds_db`

## Agent Rule

Execute one task at a time.

Do not modify unrelated architecture.

---

## Task 1 — Add Alias Package

### Goal

Create the package:

```text
src/brazilian_bonds_db/
```

### Files

```text
src/brazilian_bonds_db/__init__.py
src/brazilian_bonds_db/update.py
src/brazilian_bonds_db/readers.py
```

### Requirements

- delegate to `app.public`
- no business logic
- no heavy import side effects

---

## Task 2 — Re-export Update

### Goal

Expose:

```python
import brazilian_bonds_db as bbdb

bbdb.update()
```

### Implementation Direction

`src/brazilian_bonds_db/update.py` should import from:

```python
app.public.update
```

`src/brazilian_bonds_db/__init__.py` should expose:

```python
from .update import update
```

---

## Task 3 — Re-export `read_data`

### Goal

Expose:

```python
data = bbdb.read_data()
from brazilian_bonds_db import read_data
from brazilian_bonds_db.readers import read_data
```

### Implementation Direction

`src/brazilian_bonds_db/readers.py` should re-export from:

```python
app.public.readers.read_data
```

`src/brazilian_bonds_db/__init__.py` should expose:

```python
from .readers import read_data
```

### Do Not

- expose `GoldReader` or `read_gold` as primary symbols on `__init__.py`

---

## Task 4 — Update Packaging Configuration

### Goal

Ensure editable install includes the alias package.

### Check

```text
pyproject.toml
```

### Requirements

- `pip install -e .` should make `brazilian_bonds_db` importable
- existing `app` package remains importable

---

## Task 5 — Add Import Tests

### Suggested Test File

```text
tests/public/test_brazilian_bonds_db_alias.py
```

### Tests

```python
def test_import_alias():
    import brazilian_bonds_db as bbdb
    assert hasattr(bbdb, "update")
    assert hasattr(bbdb, "read_data")
    assert callable(bbdb.read_data)
```

Also test:

```python
from brazilian_bonds_db.readers import read_data
```

### Do Not

- assert `hasattr(bbdb, "GoldReader")` or `read_gold` as primary API requirements
