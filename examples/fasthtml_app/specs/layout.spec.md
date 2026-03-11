---
name: layout
type: bundle
status: stable
dependencies:
  - fasthtml_interface
---

# Overview

Page structure and reusable UI components for the FastHTML todo app. All functions
return FastHTML components. See `fasthtml_interface` for import and API details.

# Functions

## `home_page(todos: list[str]) -> tuple`

Returns the complete page as a tuple of top-level FastHTML components: `Title`, `H1`,
`add_form()`, and a `Ul(id="todo-list")` populated with one `todo_item(text, index)`
per entry.

The `Ul` element has `id="todo-list"` — this is the HTMX swap target for new items.

## `todo_item(text: str, index: int) -> Li`

Returns a single `Li` containing the todo text and a delete button.

The delete button:
- Uses `hx_delete=f"/todos/{index}"` to call the DELETE route
- Uses `hx_target="closest li"` and `hx_swap="outerHTML"` so HTMX removes the
  entire `<li>` from the DOM on a successful response

## `add_form() -> Form`

Returns the add-todo form with a text input (`name="item"`, placeholder text) and a
submit button. The form POSTs to `/todos` via HTMX:
- `hx_post="/todos"`
- `hx_swap="beforeend"`
- `hx_target="#todo-list"`

This inserts the returned `<li>` at the end of the list without a full page reload.

# Examples

```python
home_page([])           # returns (Title(...), H1(...), Form(...), Ul(id="todo-list"))
home_page(["Buy milk"]) # Ul contains one Li
todo_item("Walk dog", 0)  # Li with text and hx-delete="/todos/0"
add_form()              # Form with hx-post="/todos"
```
