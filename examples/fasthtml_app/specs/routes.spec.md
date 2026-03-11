---
name: routes
type: bundle
status: stable
dependencies:
  - fasthtml_interface
  - layout
  - state
---

# Overview

Route handlers for the FastHTML todo app. Creates the ASGI app and registers GET,
POST, and DELETE routes. Imports UI components from `layout` and data operations
from `state`.

The app is created at module level with Pico CSS loaded:
```python
app, rt = fast_app(hdrs=(picolink,))
```

The `if __name__ == "__main__":` guard calls `serve()` so the module is importable
by tests without starting a server.

# Routes

## `GET /`

Calls `get_todos()` from `state`, then `home_page(todos)` from `layout`.
Returns the result directly — FastHTML serialises it to HTML.

## `POST /todos`

Accepts form field `item: str`. If `item` is blank or whitespace-only, returns an
empty string. Otherwise calls `add_todo(item)` from `state` to record it, then
returns `todo_item(item, index)` from `layout` for the new list item.

HTMX appends the returned `<li>` to `#todo-list` (`hx-swap="beforeend"`).

## `DELETE /todos/{index}`

Accepts path parameter `index: int`. Calls `delete_todo(index)` from `state`.
If `index` is out of range (`IndexError`), returns HTTP 404.
Returns an empty string on success — HTMX removes the `<li>` via `hx-swap="outerHTML"`.

# Test Scenarios

| Scenario | Action | Expected |
|----------|--------|----------|
| Home page (empty) | GET / | 200, HTML contains `<ul id="todo-list">` |
| Home page (populated) | GET / after adding a todo | HTML contains `hx-delete` attribute |
| Add todo | POST /todos item="Buy milk" | 200, response contains "Buy milk" in `<li>` |
| Empty item | POST /todos item="" | 200, empty response body |
| Delete todo | DELETE /todos/0 after adding one | 200, empty body, list shrinks |
| Bad index | DELETE /todos/99 | 404 |
