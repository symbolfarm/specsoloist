# Task: Validate the FastHTML Example End-to-End

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.

The `examples/fasthtml_app/` directory contains a complete FastHTML todo app example:
- `specs/fasthtml_interface.spec.md` — type spec documenting the FastHTML Python API
- `specs/app.spec.md` — bundle spec for the todo app routes
- `arrangement.yaml` — build config (Python, uv, pytest, Starlette test client)
- `pyproject.toml` — project dependencies

**This example has never been run.** The goal of this task is to validate it end-to-end:
run `sp conduct`, make the tests pass, and document what worked and what needed fixing.

## What to Do

### 1. Inspect the existing specs and arrangement

Read all four files in `examples/fasthtml_app/` before doing anything. Understand what
the specs describe and what the arrangement expects.

### 2. Set up the environment

```bash
cd examples/fasthtml_app
uv sync         # installs python-fasthtml, pytest, starlette
```

Verify `python-fasthtml` is importable:
```bash
uv run python -c "from fasthtml.common import fast_app; print('ok')"
```

If this fails, check `pyproject.toml` and fix the dependency name (it may be
`python-fasthtml` or just `fasthtml` depending on the PyPI package name).

### 3. Validate the specs

```bash
sp validate fasthtml_interface   # from examples/fasthtml_app/
sp validate app
```

Fix any structural errors before running `sp conduct`. Quality hints (⚠) are fine to leave.

### 4. Run `sp conduct`

```bash
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
```

This will spawn a conductor agent that reads the specs, resolves the dependency order
(`fasthtml_interface` → `app`), and compiles code + tests.

Expected output locations (per arrangement):
- `src/fasthtml_interface.py` — the interface type (may be trivial or empty)
- `src/app.py` — the todo app implementation
- `tests/test_fasthtml_interface.py`
- `tests/test_app.py`

### 5. Run tests

```bash
uv run pytest tests/ -v
```

### 6. Fix any issues

If tests fail, investigate whether the issue is:

**a) Wrong API usage in generated code** — the soloist misunderstood FastHTML.
Fix by improving `fasthtml_interface.spec.md` to be more explicit, then re-run
`sp conduct` for just the failing spec:
```bash
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
```

**b) Wrong test assumptions** — the test imports something that doesn't exist, or uses
the Starlette test client incorrectly.
Fix by improving `app.spec.md`'s Test Scenarios section to be more explicit about how
tests should work.

**c) Environment issue** — missing dependency, wrong Python version, etc.
Fix `pyproject.toml` or `arrangement.yaml` accordingly.

Do not manually edit generated files in `src/` or `tests/` — always fix the spec or
arrangement and re-compile.

### 7. Write a README

Once tests pass, write `examples/fasthtml_app/README.md` documenting:
- What the example demonstrates
- Prerequisites (`uv`, `python-fasthtml`)
- How to run `sp conduct`
- How to run the tests
- How to start the app (`python src/app.py`)
- Any gotchas or FastHTML API quirks discovered during validation

## Files to Read First

- `examples/fasthtml_app/specs/fasthtml_interface.spec.md`
- `examples/fasthtml_app/specs/app.spec.md`
- `examples/fasthtml_app/arrangement.yaml`
- `examples/fasthtml_app/pyproject.toml`
- `AGENTS.md`

## Success Criteria

1. `uv run pytest examples/fasthtml_app/tests/ -v` passes with 0 failures.
2. The generated `src/app.py` is runnable: `uv run python src/app.py` starts a server on port 5001.
3. `examples/fasthtml_app/README.md` exists and covers all the points above.
4. Any changes made to `specs/` or `arrangement.yaml` are committed with a note explaining why.
5. No generated files (`src/`, `tests/`) are committed — only spec/arrangement/config changes.

## Notes on FastHTML

FastHTML is a new Python web framework and LLMs may be unfamiliar with its API.
Key points the soloist needs to know (and should be in `fasthtml_interface.spec.md`):

- Import from `fasthtml.common`, not `fasthtml`
- `app, rt = fast_app()` — creates the app and route decorator in one call
- Route handlers are decorated with `@rt("/path")`, not `@app.route`
- Handlers return HTML components directly (e.g. `return Div(P("hello"))`)
- HTMX attributes use underscores: `hx_post`, `hx_swap`, `hx_target`
- The Starlette test client: `from starlette.testclient import TestClient; client = TestClient(app)`
- `serve()` must NOT be called in test files — only in `if __name__ == "__main__"` guards

If `fasthtml_interface.spec.md` is missing any of these, add them.
