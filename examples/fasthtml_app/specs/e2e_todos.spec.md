---
name: e2e_todos
type: bundle
status: draft
dependencies:
  - layout
  - routes
---

# Overview

End-to-end browser tests for the todo app. Tests run against a live FastHTML server
using pytest-playwright. The server is started as a subprocess in a session-scoped
fixture and torn down after the test session.

This spec uses `data-testid` selectors to interact with the UI. The component spec
(`layout`) must add the following `data-testid` attributes to the rendered HTML:

- `<ul data-testid="todo-list">` — the main todo list container
- `<li data-testid="todo-item">` — each todo item row
- `<button data-testid="delete-btn">` — delete button within each `todo-item`
- `<input data-testid="todo-input">` — the text input in the add form
- `<button data-testid="add-btn">` — the submit button in the add form

The server runs on `http://localhost:5001`.

# Functions

## `live_server(tmp_path) -> str`

Pytest session-scoped fixture. Starts `python src/routes.py` from the
`examples/fasthtml_app/` directory as a subprocess. Polls
`http://localhost:5001/` every 0.5 seconds until it responds (up to 10 seconds).
Yields the base URL `"http://localhost:5001"`. Terminates the subprocess on teardown.

# Test Scenarios

| Scenario | Steps | Expected |
|----------|-------|----------|
| Page loads | Navigate to http://localhost:5001 | Page title is "Todo List", `[data-testid="todo-list"]` is present |
| Add todo | Fill "Buy milk" in `[data-testid="todo-input"]`, click `[data-testid="add-btn"]` | "Buy milk" appears inside `[data-testid="todo-list"]` |
| Add todo clears input | Fill "Buy milk", click Add | Input is empty after submission |
| Delete todo | Add "Buy milk", click `[data-testid="delete-btn"]` on the item | Item disappears from `[data-testid="todo-list"]` |
| Empty add | Click `[data-testid="add-btn"]` with empty input | `[data-testid="todo-list"]` has no new items |

# Implementation Notes

Generate `tests/test_e2e_todos.py` using `pytest-playwright`:

1. **Session fixture `live_server`**: Start `python src/routes.py` as a subprocess.
   Poll `http://localhost:5001/` until it responds (up to 10 seconds), then yield
   the base URL. Terminate the process on teardown.

2. **State independence**: Write tests that are independent — each test adds its own
   data before asserting. Do not rely on state from previous tests.

3. **Selectors**: Use `page.locator('[data-testid="..."]')` exclusively.

4. **Waiting for HTMX**: Use `page.wait_for_selector('[data-testid="todo-item"]')`
   after clicking Add to wait for HTMX to inject the new item.
