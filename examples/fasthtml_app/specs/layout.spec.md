---
name: layout
type: bundle
status: stable
dependencies:
  - fasthtml_interface
---

# Overview

Page structure and reusable UI components for the FastHTML todo app. Uses Pico CSS
(loaded via `picolink`) for clean styling with no custom CSS. All functions return
FastHTML components. See `fasthtml_interface` for import and API details.

# Functions

## `home_page(todos: list[str]) -> tuple`

Returns the complete page as a tuple of top-level FastHTML components:
- `Title("Todo List")`
- `Main(..., cls="container")` containing:
  - `H1("Todo List")`
  - `add_form()`
  - `Ul(id="todo-list")` populated with one `todo_item(text, index)` per entry,
    or a `P("No todos yet. Add one above!", id="empty-msg")` if the list is empty

The `Ul` element has `id="todo-list"` — this is the HTMX swap target for new items.

## `todo_item(text: str, index: int) -> Li`

Returns a single `Li` containing the todo text and a delete button arranged inline
(e.g. using `style="display:flex; justify-content:space-between; align-items:center"`).

The delete button:
- Labelled `"✕"` (or similar compact label)
- Uses `hx_delete=f"/todos/{index}"` to call the DELETE route
- Uses `hx_target="closest li"` and `hx_swap="outerHTML"` so HTMX removes the
  entire `<li>` from the DOM on a successful response
- Styled as a small secondary/outline button (e.g. `cls="secondary outline"` for Pico CSS,
  or minimal inline style)

## `add_form() -> Form`

Returns the add-todo form with:
- A text input (`name="item"`, `placeholder="What needs doing?"`, `autofocus=True`)
- A submit button labelled `"Add"`

The form submits via HTMX:
- `hx_post="/todos"`
- `hx_swap="beforeend"`
- `hx_target="#todo-list"`
- `hx_on__after_request="this.reset()"` — clears the input field after each successful add

# Examples

```python
home_page([])           # Main contains empty-msg paragraph, empty Ul
home_page(["Buy milk"]) # Ul contains one Li with text and delete button
todo_item("Walk dog", 2)  # Li with "Walk dog", hx-delete="/todos/2"
add_form()              # Form with hx-post="/todos" and reset-on-submit
```
