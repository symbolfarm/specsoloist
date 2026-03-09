---
name: app
type: module
status: draft
dependencies:
  - fasthtml_interface
---

# Overview

A minimal todo list web app built with FastHTML and HTMX.

# FastHTML Todo App

A minimal todo list web app built with FastHTML and HTMX. Routes return HTML fragments
that HTMX swaps into the page without a full reload.

## `GET /`

Returns the full page: a heading, a form to add todos, and an empty `<ul id="todo-list">`.

**Returns:** `Title`, `H1`, `Form`, `Ul` components assembled into a full page.

## `POST /todos`

Accepts a form POST with a single field `item` (the todo text).

- Appends an `<li>` containing the todo text to the in-memory todo list.
- Returns only the new `<li>` element (HTMX swaps it into `#todo-list`).
- Ignores empty or whitespace-only `item` values (returns an empty string).

**Form fields:** `item: str`
**Returns:** An `Li` component, or an empty string if `item` is blank.

## `DELETE /todos/{index}`

Removes the todo at the given index from the in-memory list.

- If `index` is out of range, returns HTTP 404.
- Returns an empty string on success (HTMX removes the element via `hx-swap="outerHTML"`).

**Path params:** `index: int`
**Returns:** Empty string, or HTTP 404.

## State

Todos are stored in a module-level list `todos: list[str]`. This is intentionally simple —
no database, no persistence across restarts.

## Test Scenarios

| Scenario | Action | Expected |
|----------|--------|----------|
| Home page | GET / | Returns HTML containing `<ul id="todo-list">` |
| Add todo | POST /todos item="Buy milk" | Returns `<li>` containing "Buy milk" |
| Empty item | POST /todos item="" | Returns empty string |
| Delete todo | DELETE /todos/0 (after adding one) | Returns empty string, list shrinks |
| Bad index | DELETE /todos/99 | Returns 404 |
