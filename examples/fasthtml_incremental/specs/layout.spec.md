---
name: layout
type: bundle
status: stable
dependencies:
  - state
---

# Overview

UI components for the priority todo app. All functions return FastHTML elements.
Import from `fasthtml.common`. Uses Pico CSS via `picolink`.

Priority values are "low", "medium", "high" with distinct badge colours:
- low → grey (#6c757d)
- medium → orange (#fd7e14)
- high → red (#dc3545)

# Functions

## `priority_badge(priority: str) -> Span`

Return a coloured inline badge showing the priority label. Styled as a small
coloured pill with white text.

## `todo_item_row(todo: dict, index: int) -> Li`

Return a single `<li data-testid="todo-item">` containing:
- A `priority_badge` for the todo's priority
- The todo text
- A delete button `<button data-testid="delete-btn">✕</button>` that calls
  `hx_delete=f"/todos/{index}"`, targets `closest li`, swaps `outerHTML`

## `add_todo_form() -> Form`

Return the form for adding a new todo:
- Text input (`name="text"`, `placeholder="What needs doing?"`, `autofocus=True`,
  `data_testid="todo-input"`)
- Priority select (`name="priority"`) with options Low/Medium/High; Medium pre-selected
- Submit button (`data_testid="add-btn"`) labelled "Add"

Form submits via HTMX: `hx_post="/todos"`, `hx_swap="beforeend"`,
`hx_target="#todo-list"`, `hx_on__after_request="this.reset()"`.

## `filter_links(current: str) -> Div`

Return a navigation row with links to filter todos by priority:
- "All" → href="/"
- "Low" → href="/?priority=low"
- "Medium" → href="/?priority=medium"
- "High" → href="/?priority=high"

The currently active filter is styled bold.

## `home_page(todos: list[dict], current_filter: str = "all") -> tuple`

Return the complete page as a tuple of FastHTML elements:
- `Title("Priority Todos")`
- `Main(cls="container")` containing:
  - `H1("Priority Todos")`
  - `add_todo_form()`
  - `filter_links(current_filter)`
  - `Ul(id="todo-list", data_testid="todo-list")` populated with one
    `todo_item_row(t, i)` per todo, or a "No todos yet" paragraph if empty

## `stats_page(counts: dict[str, int]) -> tuple`

Return the stats page:
- `Title("Todo Stats")`
- `Main(cls="container")` containing an `H1`, a back link to "/", a count of total todos,
  and a table with rows for each priority and its count.

# Examples

```python
priority_badge("high")    # Span with red background
todo_item_row({"text": "Fix bug", "priority": "high"}, 0)  # Li with badge and delete btn
add_todo_form()           # Form with text input, priority select, add button
filter_links("high")      # Div with 4 links; "High" is bold
home_page([], "all")      # Main with empty list and "No todos" message
home_page([{"text": "A", "priority": "low"}], "all")  # Main with one item
```
