# FastHTML Todo App — SpecSoloist Example

A minimal todo list web app built with [FastHTML](https://fastht.ml) and HTMX,
generated entirely from specs by SpecSoloist.

## What This Demonstrates

- **Three-spec decomposition**: separate data model (`state`), UI components (`layout`),
  and HTTP handlers (`routes`) — each independently testable
- **Reference spec**: `fasthtml_interface` documents the FastHTML API without generating
  any code — soloists read it as context so they use the API correctly
- **Dependency ordering**: the conductor compiles specs in order:
  `state` → `layout` → `routes` (with `fasthtml_interface` injected as context)
- **UI completeness tests**: `test_routes.py` verifies that the home page contains
  `hx-delete` attributes — the kind of test that catches "button exists in spec but
  not in rendered HTML" bugs

## Why Three Specs?

A single `app.spec.md` can describe routes, but it can't easily verify that the UI
renders correctly. By separating concerns:

- `state.spec.md` — pure data logic, testable with no HTTP or HTML
- `layout.spec.md` — UI components, testable by rendering to strings and checking attributes
- `routes.spec.md` — route handlers, testable via Starlette TestClient

This decomposition catches the "delete button gap": the DELETE route can pass its tests
while the home page never actually renders a delete button. With `layout` and `routes`
as separate specs, the layout tests verify the button exists and `test_routes.py` verifies
it appears in the rendered response.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) — Python package manager
- `sp` (SpecSoloist CLI) — install via `pip install specsoloist` or from the project root

## Running `sp conduct`

```bash
cd examples/fasthtml_app
uv sync                    # install python-fasthtml, pytest, httpx
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
```

The conductor resolves dependencies and generates:

| File | From spec | Description |
|------|-----------|-------------|
| `src/state.py` | `state.spec.md` | In-memory todo list: `add_todo`, `delete_todo`, `get_todos` |
| `src/layout.py` | `layout.spec.md` | FastHTML components: `home_page`, `todo_item`, `add_form` |
| `src/routes.py` | `routes.spec.md` | Route handlers: GET /, POST /todos, DELETE /todos/{index} |
| `tests/test_state.py` | — | Unit tests for state module (no HTTP) |
| `tests/test_layout.py` | — | Render tests for UI components |
| `tests/test_routes.py` | — | Integration tests via Starlette TestClient |

No `src/fasthtml_interface.py` is generated — `fasthtml_interface` is a `type: reference`
spec. Its contents are injected into soloist prompts as API documentation.

## Running the Tests

```bash
uv run pytest tests/ -v
```

Expected: **53 passed, 0 failed**.

## Starting the App

```bash
uv run python src/routes.py
```

Opens on `http://localhost:5001`. Add todos via the form; delete them with the ✕ button.
Both actions use HTMX — no full page reload.

## What `type: reference` Means

`fasthtml_interface.spec.md` has `type: reference` in its frontmatter. This tells
SpecSoloist:

1. **No implementation generated** — there is no `fasthtml_interface.py` to write; the
   library already exists on PyPI
2. **Injected as context** — any spec that lists `fasthtml_interface` as a dependency
   gets its full content injected into the soloist prompt, so the agent knows the exact
   API to use
3. **Verified documentation** — the `# Verification` section is compiled into a test
   that imports the library and checks its API hasn't drifted

This pattern replaces the old workaround of using `type: bundle` with a `yaml:functions`
block to describe third-party APIs.

## FastHTML API Quirks

Captured in `specs/fasthtml_interface.spec.md`:

- **Import from `fasthtml.common`**, not `fasthtml`:
  ```python
  from fasthtml.common import fast_app, serve, Div, P, H1, Form, Input, Button, Title, Ul, Li
  ```
- **`app, rt = fast_app()`** — returns the ASGI app and a route decorator factory.
- **Route handlers** are decorated with `@rt("/path")`, not `@app.route`.
- **HTMX attributes** use underscores: `hx_post`, `hx_swap`, `hx_target`, `hx_delete`.
- **`serve()` must be guarded**: `if __name__ == "__main__": serve()`.
  Calling it at module level blocks test collection.
- **Starlette test client** works because FastHTML's ASGI app is Starlette-compatible.
