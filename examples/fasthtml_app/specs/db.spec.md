---
name: db
type: bundle
status: stable
dependencies:
  - fastlite_interface
---

# Overview

Database-backed data access layer for the FastHTML todo app. Replaces the in-memory
`state` module with a persistent SQLite database via fastlite.

No FastHTML or HTTP imports. This module is independently testable using an in-memory
database. Tests should pass a database path of `":memory:"` to `open_db()`.

# Data Model

## `Todo` dataclass

```python
from dataclasses import dataclass

@dataclass
class Todo:
    id: int         # primary key — set to None on insert; fastlite assigns it
    text: str
    done: bool = False
```

# Functions

## `open_db(path: str = "todos.db") -> tuple[Database, Table]`

Opens (or creates) the database at `path` and ensures the `todos` table exists.
Returns `(db, todos)` where `db` is the fastlite `Database` and `todos` is the
`Table` object for `Todo` rows.

Calling `open_db(":memory:")` returns an in-memory database suitable for tests.

## `get_todos(todos: Table) -> list[Todo]`

Returns all todos as a list of `Todo` instances, ordered by insertion order (oldest first).

## `add_todo(todos: Table, text: str) -> Todo`

Inserts a new todo with `done=False`. Returns the inserted `Todo` with its assigned `id`.

Raises `ValueError` if `text` is empty or whitespace-only.

## `delete_todo(todos: Table, id: int) -> None`

Deletes the todo with the given `id`. Raises `NotFoundError` (from fastlite) if `id`
does not exist.

## `toggle_todo(todos: Table, id: int) -> Todo`

Flips the `done` flag on the todo with `id`. Returns the updated `Todo`.

Raises `NotFoundError` if `id` does not exist.

# Examples

| Scenario | Action | Expected |
|----------|--------|----------|
| Add todo | `add_todo(todos, "Buy milk")` | Returns `Todo` with `id` set, `done=False` |
| Empty text | `add_todo(todos, "  ")` | Raises `ValueError` |
| Get todos | `add_todo(...)` × 2, `get_todos(todos)` | List of 2 `Todo` instances |
| Delete | `add_todo(...)`, `delete_todo(todos, id)` | `get_todos()` returns empty list |
| Delete missing | `delete_todo(todos, 99)` | Raises `NotFoundError` |
| Toggle | `add_todo(...)`, `toggle_todo(todos, id)` | Returns `Todo` with `done=True` |
| Toggle twice | `toggle_todo` × 2 | `done` returns to `False` |

# Test Fixture Pattern

```python
import pytest
from db import open_db, Todo

@pytest.fixture
def todos():
    _, todos = open_db(":memory:")
    return todos
```

Pass the `todos` fixture directly to each test function. Each test gets a fresh,
empty table with no setup or teardown needed.
