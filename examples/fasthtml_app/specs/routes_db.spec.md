---
name: routes_db
type: bundle
status: stable
dependencies:
  - fasthtml_interface
  - layout
  - db
---

# Overview

Route handlers for the database-backed FastHTML todo app. Extends the in-memory `routes`
module by using the `db` module for persistence. Each todo now has an `id` (SQLite primary
key) rather than a list index, and a `done`/`undone` toggle in addition to delete.

The database is opened once at module level:

```python
from db import open_db
_db, todos = open_db()
```

App is created at module level: `app, rt = fast_app(hdrs=(picolink,))`

The `if __name__ == "__main__":` guard calls `serve()` for local development.

# Routes

## `GET /`

Calls `db.get_todos(todos)` and passes the result to `layout.home_page(todo_list)`.
Returns the result.

## `POST /todos`

Accepts form field `item: str`. If blank or whitespace-only, returns empty string.
Otherwise calls `db.add_todo(todos, item)` and returns `layout.todo_item(new_todo.text, new_todo.id)`
so HTMX can append it to `#todo-list`.

## `DELETE /todos/{id}`

Accepts path parameter `id: int`. Calls `db.delete_todo(todos, id)`.
If `NotFoundError` is raised, returns HTTP 404.
Returns empty string on success — HTMX removes the row via `hx-swap="outerHTML"`.

## `PUT /todos/{id}/toggle`

Accepts path parameter `id: int`. Calls `db.toggle_todo(todos, id)`.
If `NotFoundError` is raised, returns HTTP 404.
Returns `layout.todo_item(todo.text, todo.id)` with the updated done state — HTMX
replaces the row via `hx-swap="outerHTML"`.

# Layout Contract

Routes use `layout.home_page(todos)` and `layout.todo_item(text, id)`. The `id` is used
in place of a list index for HTMX delete/toggle targets (`/todos/{id}`).

The `layout` module must render a toggle button:
```
<button hx-put="/todos/{id}/toggle" hx-target="closest li" hx-swap="outerHTML">
  Toggle
</button>
```

# Test Scenarios

| Scenario | Action | Expected |
|----------|--------|----------|
| Home page empty | GET / | 200, HTML contains `id="todo-list"` |
| Add todo | POST /todos item="Buy milk" | 200, response contains "Buy milk" |
| Empty item | POST /todos item="" | 200, empty body |
| Delete todo | POST then DELETE /todos/{id} | 200, empty body |
| Delete missing | DELETE /todos/99 | 404 |
| Toggle todo | POST then PUT /todos/{id}/toggle | 200, response contains todo text |
| Toggle missing | PUT /todos/99/toggle | 404 |

# Notes

Tests should use a fresh in-memory database for each test. The module-level `todos`
table must be replaceable for testing. The recommended pattern: expose a
`set_todos_table(t)` helper, or accept an optional `db_path` parameter in a factory
function. Alternatively, tests can patch the module-level `todos` with a test table
created from `open_db(":memory:")`.
