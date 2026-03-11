# FastHTML Todo App — SpecSoloist Example

A minimal todo list web app built with [FastHTML](https://fastht.ml) and HTMX,
generated entirely from specs by SpecSoloist.

## What This Demonstrates

- A two-spec project: an **interface spec** (`fasthtml_interface`) and an **app spec** (`app`)
- Dependency ordering: the conductor compiles `fasthtml_interface` before `app`
- How to document a third-party API in a spec so soloists use it correctly
- Testing a FastHTML app with the Starlette test client

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) — Python package manager
- `sp` (SpecSoloist CLI) — install via `pip install specsoloist` or from the project root

## Running `sp conduct`

```bash
cd examples/fasthtml_app
uv sync                    # install python-fasthtml, pytest, httpx
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
```

The conductor resolves the dependency order (`fasthtml_interface` → `app`) and generates:

| File | Description |
|------|-------------|
| `src/fasthtml_interface.py` | Re-exports FastHTML symbols from `fasthtml.common` |
| `src/app.py` | Todo app with GET /, POST /todos, DELETE /todos/{index} |
| `tests/test_fasthtml_interface.py` | Import and render tests |
| `tests/test_app.py` | Route tests using Starlette TestClient |

## Running the Tests

```bash
uv run pytest tests/ -v
```

Expected: **23 passed, 0 failed**.

## Starting the App

```bash
uv run python src/app.py
```

Opens on `http://localhost:5001`. Add todos via the form; they appear instantly via HTMX
without a page reload.

## FastHTML API Quirks

Discovered during validation — captured in `specs/fasthtml_interface.spec.md`:

- **Import from `fasthtml.common`**, not `fasthtml`:
  ```python
  from fasthtml.common import fast_app, serve, Div, P, H1, Form, Input, Button, Title, Ul, Li
  ```
- **`app, rt = fast_app()`** — returns the ASGI app and a route decorator factory in one call.
- **Route handlers** are decorated with `@rt("/path")`, not `@app.route`.
- **HTMX attributes** use underscores: `hx_post`, `hx_swap`, `hx_target`.
- **`serve()` must be guarded** — place inside `if __name__ == "__main__": serve()`.
  Calling it at module level will block test collection.
- **Starlette test client** works because FastHTML's ASGI app is Starlette-compatible:
  ```python
  from starlette.testclient import TestClient
  client = TestClient(app)
  ```

## Spec Changes Made During Validation

`specs/fasthtml_interface.spec.md` was changed from `type: type` to `type: bundle`
and given a proper `yaml:functions` block. The original `type: type` was incorrect
(this is API documentation, not a data type) and failed `sp validate`. The bundle
format lets soloists see each function's signature and behavior inline.
