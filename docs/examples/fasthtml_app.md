# FastHTML Todo App (Python)

`examples/fasthtml_app/` is a minimal todo list web app built with
[FastHTML](https://fastht.ml) and HTMX, generated entirely from specs. It is one of
SpecSoloist's two primary validated examples.

## What it demonstrates

- **Three-spec decomposition**: separate data model (`state`), UI components (`layout`),
  and HTTP handlers (`routes`) — each independently testable
- **`type: reference` spec**: `fasthtml_interface` documents the FastHTML API without
  generating any code — soloists read it as context so they use the real API correctly
- **Dependency ordering**: the conductor compiles `state` → `layout` → `routes`, with
  `fasthtml_interface` injected as context into each
- **UI completeness testing**: `test_routes.py` verifies that the home page renders
  `hx-delete` attributes — catching the case where a DELETE route passes its own tests
  but the button never appears in the rendered HTML

## Spec structure

| Spec | Type | Description |
|------|------|-------------|
| `fasthtml_interface` | `reference` | FastHTML API docs (no code generated) |
| `state` | `bundle` | In-memory todo list: `add_todo`, `delete_todo`, `get_todos` |
| `layout` | `bundle` | FastHTML components: `home_page`, `todo_item`, `add_form` |
| `routes` | `bundle` | Route handlers: `GET /`, `POST /todos`, `DELETE /todos/{index}` |

## Running it

```bash
cd examples/fasthtml_app
uv sync
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
uv run python -m pytest tests/ -v
```

Expected: **23 tests passed** across `test_state.py`, `test_layout.py`,
`test_routes.py`.

## Why three specs?

A single `app.spec.md` can describe routes, but it can't easily verify that the UI
renders correctly. Separating concerns means:

- `state.spec.md` — pure data logic, testable with no HTTP or HTML
- `layout.spec.md` — UI components, testable by rendering to strings and checking attributes
- `routes.spec.md` — route handlers, testable via Starlette `TestClient`

This decomposition catches the "delete button gap": the DELETE route can pass its tests
while the home page never actually renders a delete button. With layout and routes as
separate specs, the layout tests verify the button exists and `test_routes.py` verifies
it appears in the rendered response.

## Database variant

`examples/fasthtml_app/specs/` also includes `db.spec.md`, `routes_db.spec.md`, and
`fastlite_interface.spec.md` — a database-backed version using
[fastlite](https://github.com/AnswerDotAI/fastlite). See [Database Patterns](../database-patterns.md)
for the full pattern.
