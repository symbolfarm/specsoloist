"""A FastHTML todo app with priorities — written without SpecSoloist.

This is the "before" state: a working app with no specs. The incremental
adoption guide shows how to extract specs from this code using sp respec.

Run with:
  cd examples/fasthtml_incremental
  uv run python original/app.py
"""

from fasthtml.common import (
    Div, H1, H2, Form, Input, Button, Select, Option, Ul, Li, P,
    Table, Thead, Tbody, Tr, Th, Td, Span, Title, Main, A,
    fast_app, picolink, serve,
)
from starlette.responses import Response

app, rt = fast_app(hdrs=(picolink,))

# In-memory store: list of {"text": str, "priority": str}
todos: list[dict] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PRIORITIES = ("low", "medium", "high")


def priority_badge(priority: str) -> Span:
    """Return a coloured badge for the given priority level."""
    colors = {"low": "#6c757d", "medium": "#fd7e14", "high": "#dc3545"}
    return Span(
        priority,
        style=(
            f"background:{colors.get(priority, '#6c757d')};"
            "color:white;padding:2px 8px;border-radius:4px;"
            "font-size:0.8em;margin-right:8px;"
        ),
    )


def todo_item_row(todo: dict, index: int) -> Li:
    """Render a single todo as a list item."""
    return Li(
        Div(
            priority_badge(todo["priority"]),
            Span(todo["text"]),
            Button(
                "✕",
                hx_delete=f"/todos/{index}",
                hx_target="closest li",
                hx_swap="outerHTML",
                style="float:right;padding:2px 8px;",
                cls="secondary outline",
            ),
            style="display:flex;align-items:center;",
        ),
        data_testid="todo-item",
    )


def add_todo_form() -> Form:
    """Return the form for adding a new todo with priority."""
    return Form(
        Input(name="text", placeholder="What needs doing?", autofocus=True),
        Select(
            Option("Low", value="low"),
            Option("Medium", value="medium", selected=True),
            Option("High", value="high"),
            name="priority",
        ),
        Button("Add"),
        hx_post="/todos",
        hx_swap="beforeend",
        hx_target="#todo-list",
        hx_on__after_request="this.reset()",
    )


def filter_links(current: str) -> Div:
    """Return filter navigation links."""
    filters = [("all", "All"), ("low", "Low"), ("medium", "Medium"), ("high", "High")]
    links = []
    for value, label in filters:
        href = "/" if value == "all" else f"/?priority={value}"
        style = "font-weight:bold;" if value == current else ""
        links.append(A(label, href=href, style=f"margin-right:8px;{style}"))
    return Div(*links, style="margin-bottom:1rem;")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@rt("/")
def get(priority: str = ""):
    """Home page: list todos, optionally filtered by priority."""
    items = todos
    current_filter = priority or "all"
    if priority in PRIORITIES:
        items = [t for t in todos if t["priority"] == priority]

    if items:
        todo_list = Ul(
            *[todo_item_row(t, i) for i, t in enumerate(todos) if not priority or t["priority"] == priority],
            id="todo-list",
        )
    else:
        todo_list = Ul(
            P("No todos yet. Add one above!" if not priority else f"No {priority} priority todos.", id="empty-msg"),
            id="todo-list",
        )

    return (
        Title("Priority Todos"),
        Main(
            H1("Priority Todos"),
            add_todo_form(),
            filter_links(current_filter),
            todo_list,
            cls="container",
        ),
    )


@rt("/todos")
def post(text: str, priority: str = "medium"):
    """Add a new todo. Ignores blank text."""
    if not text or not text.strip():
        return ""
    if priority not in PRIORITIES:
        priority = "medium"
    todos.append({"text": text.strip(), "priority": priority})
    index = len(todos) - 1
    return todo_item_row({"text": text.strip(), "priority": priority}, index)


@rt("/todos/{index}")
def delete(index: int):
    """Delete a todo by index. Returns 404 if out of range."""
    if index < 0 or index >= len(todos):
        return Response("Not found", status_code=404)
    todos.pop(index)
    return ""


@rt("/stats")
def stats():
    """Statistics endpoint: count per priority and total."""
    counts = {"low": 0, "medium": 0, "high": 0}
    for todo in todos:
        p = todo.get("priority", "medium")
        if p in counts:
            counts[p] += 1

    return (
        Title("Todo Stats"),
        Main(
            H1("Statistics"),
            A("← Back", href="/"),
            H2(f"Total: {len(todos)}"),
            Table(
                Thead(Tr(Th("Priority"), Th("Count"))),
                Tbody(
                    *[Tr(Td(p.capitalize()), Td(str(c))) for p, c in counts.items()]
                ),
            ),
            cls="container",
        ),
    )


if __name__ == "__main__":
    serve()
