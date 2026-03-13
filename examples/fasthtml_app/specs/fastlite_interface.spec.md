---
name: fastlite_interface
type: reference
status: stable
---

# Overview

The subset of [fastlite](https://github.com/AnswerDotAI/fastlite) used in this project.
fastlite is a lightweight SQLite ORM bundled with `python-fasthtml` (`>= 0.12`). Specs that
perform database operations should list `fastlite_interface` as a dependency. No implementation
is generated from this spec — it is API documentation only.

fastlite is relatively unknown and LLMs reliably hallucinate its API (often generating
SQLAlchemy or raw `sqlite3` calls instead). This reference spec prevents that.

**Import:** `from fastlite import database` — fastlite ships inside python-fasthtml; no
separate install needed.

# API

## Opening a Database

```python
from fastlite import database

db = database("todos.db")    # opens (or creates) todos.db in the current directory
db = database(":memory:")    # in-memory database — useful for tests
```

`database(path)` returns a `Database` object. The file is created if it does not exist.

## Defining a Table Schema

Use a standard Python `dataclass` to define the schema. Field names become column names.
Mark the primary key with `pk=` when registering the table:

```python
from dataclasses import dataclass

@dataclass
class Todo:
    id: int
    text: str
    done: bool = False

todos = db.create(Todo, pk='id')   # registers the table, creates it if absent
```

`db.create(cls, pk)` creates the table if it doesn't exist and returns a `Table` object.
Subsequent calls to `db.create()` with the same class are idempotent.

## Table Operations

All operations are on the `Table` object returned by `db.create()`.

### Insert

```python
todo = todos.insert(Todo(id=None, text="Buy milk", done=False))
# Returns the inserted Todo with id populated by SQLite autoincrement
```

Pass a dataclass instance. The `id` field should be `None` (or `0`) when inserting a new row —
SQLite assigns the `id` automatically.

### Get by Primary Key

```python
todo = todos[1]     # returns a Todo dataclass instance
todos[99]           # raises NotFoundError if id 99 doesn't exist
```

### Update

```python
todo.done = True
todos.update(todo)   # returns the updated Todo
```

### Delete

```python
todos.delete(1)      # deletes by primary key value
```

### All Rows

```python
all_todos = todos()   # returns a list of Todo instances
```

### Filtered Query

```python
done_todos = todos.where("done = ?", [True])   # returns a list of matching Todo instances
```

`where(condition, params)` takes a SQL fragment (condition only, no `WHERE` keyword) and
an optional list of parameters.

## Error Handling

```python
from fastlite import NotFoundError

try:
    todos[99]
except NotFoundError:
    ...    # id 99 doesn't exist
```

## Test Pattern (Temporary Database)

Use `":memory:"` for fast, isolated tests. Each test that needs a fresh database should
create its own `database(":memory:")` instance:

```python
import pytest
from fastlite import database

@pytest.fixture
def db():
    db = database(":memory:")
    todos = db.create(Todo, pk='id')
    return db, todos
```

Alternatively, use `tempfile.NamedTemporaryFile` with `delete=False` for file-based tests
(useful when you need to test persistence across connections), and call `os.unlink(path)`
in teardown.

# Verification

```python
from fastlite import database, NotFoundError
from dataclasses import dataclass

@dataclass
class Item:
    id: int
    name: str

db = database(":memory:")
items = db.create(Item, pk='id')

inserted = items.insert(Item(id=None, name="hello"))
assert inserted.name == "hello"
assert inserted.id is not None

fetched = items[inserted.id]
assert fetched.name == "hello"

all_items = items()
assert len(all_items) == 1

items.delete(inserted.id)
try:
    items[inserted.id]
    assert False, "should have raised"
except NotFoundError:
    pass
```
