---
name: routes
type: bundle
status: stable
dependencies:
  - state
  - layout
---

# Overview

HTTP route handlers for the priority todo app. Creates the FastHTML ASGI app and
registers GET, POST, DELETE routes plus a stats page. Imports from `state` and `layout`.

App is created at module level: `app, rt = fast_app(hdrs=(picolink,))`

The `if __name__ == "__main__":` guard calls `serve()` for local development.

# Routes

## `GET /`

Accepts optional query parameter `priority: str = ""`.

Calls `state.get_todos(priority)` to get (optionally filtered) todos. Calls
`layout.home_page(todos, current_filter)` and returns the result.

`current_filter` is `priority` if it's a valid priority string, else `"all"`.

## `GET /stats`

Calls `state.get_stats()` and passes the result to `layout.stats_page(counts)`.

## `POST /todos`

Accepts form fields `text: str` and `priority: str = "medium"`.

If `text` is blank or whitespace-only, return an empty string.
Otherwise call `state.add_todo(text, priority)` to store it, then return
`layout.todo_item_row({"text": text, "priority": priority}, index)`.

HTMX appends the returned `<li>` to `#todo-list`.

## `DELETE /todos/{index}`

Accepts path parameter `index: int`.

Call `state.delete_todo(index)`. If `IndexError` is raised, return HTTP 404.
Return an empty string on success — HTMX removes the row via `hx-swap="outerHTML"`.

# Test Scenarios

| Scenario | Action | Expected |
|----------|--------|----------|
| Home page empty | GET / | 200, HTML contains `id="todo-list"` |
| Home page with todos | GET / after adding one | HTML contains todo text and priority badge |
| Filter by priority | GET /?priority=high | Only high-priority todos in response |
| Add todo | POST /todos text="Buy milk" priority="low" | 200, response has "Buy milk" in `<li>` |
| Empty add | POST /todos text="" | 200, empty body |
| Delete todo | DELETE /todos/0 after adding one | 200, empty body |
| Bad index | DELETE /todos/99 | 404 |
| Stats page | GET /stats after adding todos | 200, contains count table |
