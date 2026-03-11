# Task: Refactor FastHTML Example — Multi-Spec Layout + Delete UI

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.

`examples/fasthtml_app/` was validated end-to-end in an earlier session (23 tests passing).
However, two structural issues were identified that make it a poor reference example:

1. **Single `app.spec.md` mixes routing with layout.** The DELETE route (`DELETE /todos/{index}`)
   was specced, the route handler works, but the home page has no delete button. The test suite
   verified the route exists but never checked the UI — the gap was invisible at the spec level.
   This is exactly the class of bug that proper spec decomposition prevents.

2. **`fasthtml_interface.spec.md` uses `type: bundle` as a workaround.** Once task 04
   (`reference` spec type) is complete, this should use `type: reference`.

This task refactors the example to demonstrate best practices for web app spec design.
It assumes task 04 (`reference` spec type) is complete.

## What to Do

### 1. Migrate `fasthtml_interface` to `type: reference`

Update `examples/fasthtml_app/specs/fasthtml_interface.spec.md`:
- Change `type: bundle` → `type: reference`
- Remove the `yaml:functions` block entirely
- Ensure `# Overview` and `# API` sections are present and complete
- The `# API` section should read as clean human-readable documentation — functions,
  their signatures, common patterns, gotchas — not YAML

Keep all the content from the current `# Behavior` section (route handler patterns, test client
examples). The `# API` section can absorb it.

### 2. Split `app.spec.md` into three specs

Delete `specs/app.spec.md` and replace it with:

**`specs/layout.spec.md`** (`type: bundle`, depends on `fasthtml_interface`)

Describes the page structure and reusable UI components:

- `home_page(todos: list[str]) -> tuple` — full page: `Title`, `H1`, form to add todos,
  `Ul(id="todo-list")` populated with one `todo_item()` per entry. The `Ul` is the HTMX
  swap target for new items (`hx_swap="beforeend"`).
- `todo_item(text: str, index: int) -> Li` — one list item: the todo text and a delete
  button. The delete button should use `hx_delete=f"/todos/{index}"` and
  `hx_swap="outerHTML"` so HTMX removes the `<li>` from the DOM on success.
- `add_form() -> Form` — the add-todo form with a text input (name="item") and submit button,
  POSTing to `/todos` with `hx_swap="beforeend"` targeting `#todo-list`.

**`specs/routes.spec.md`** (`type: bundle`, depends on `fasthtml_interface`, `layout`)

Describes the route handlers:

- `GET /` — calls `home_page(todos)` and returns the result
- `POST /todos` — accepts `item: str`, appends to `todos` if non-blank, returns
  `todo_item(text, index)` for the new item; returns empty string for blank input
- `DELETE /todos/{index}` — removes item at index from `todos`; returns 404 if out of range,
  empty string on success

Module-level state: `todos: list[str] = []`. Both routes share this list.

The app is created at module level: `app, rt = fast_app()`. The `if __name__ == "__main__":`
guard calls `serve()`.

**`specs/state.spec.md`** (`type: bundle`)

Describes the in-memory data model:

- `todos: list[str]` — module-level list, initially empty
- `add_todo(item: str) -> int` — appends item, returns new index
- `delete_todo(index: int)` — removes item at index; raises `IndexError` if out of range
- `get_todos() -> list[str]` — returns copy of current list

`routes.py` imports from `state.py` rather than managing its own list directly. This
makes `state.py` independently testable.

### 3. Update `arrangement.yaml`

The arrangement's `output_paths` already uses `{name}` substitution. No changes needed for
output paths. Update `constraints` to mention the three-spec decomposition and reference type.

If task 05 is also complete, add `dependencies` to the environment block.

### 4. Re-run `sp conduct` and validate

```bash
cd examples/fasthtml_app
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
uv run pytest tests/ -v
```

Expected output files:
- `src/layout.py`
- `src/routes.py`
- `src/state.py`
- `tests/test_layout.py`
- `tests/test_routes.py`
- `tests/test_state.py`

No `src/fasthtml_interface.py` or `tests/test_fasthtml_interface.py` (reference type generates
no code).

### 5. Verify the delete button exists in the UI

In `tests/test_routes.py`, ensure there is a test:
- `GET /` with pre-populated todos returns HTML containing `hx-delete` attributes

This is the test that was missing in the original version and that catches the "delete button
gap" class of bug.

### 6. Update `examples/fasthtml_app/README.md`

Update to reflect:
- Three-spec decomposition (layout / routes / state) and why it matters
- `fasthtml_interface` is now a `reference` spec — explain what that means
- New test count and which files are generated

## Files to Read First

- `examples/fasthtml_app/specs/` — all current specs
- `examples/fasthtml_app/arrangement.yaml`
- `examples/fasthtml_app/README.md`
- `score/spec_format.spec.md` — reference type definition (added in task 04)
- `AGENTS.md`

## Success Criteria

1. `sp validate` passes on all three new specs and on `fasthtml_interface.spec.md`.
2. `uv run pytest examples/fasthtml_app/tests/ -v` passes with 0 failures.
3. `tests/test_routes.py` includes a test that `GET /` returns HTML containing `hx-delete`.
4. `src/fasthtml_interface.py` is NOT generated (reference spec, no code output).
5. `src/state.py` is independently testable — `tests/test_state.py` tests `add_todo`,
   `delete_todo`, and `get_todos` without involving HTTP.
6. `uv run python src/routes.py` starts a server on port 5001.
7. `examples/fasthtml_app/README.md` is updated.
8. No generated files committed; spec/arrangement/README changes committed.

## Why This Matters

This refactored example becomes the canonical reference for "how to spec a web app in
SpecSoloist." New users starting a FastHTML project should be able to clone it and understand:
- What level of granularity to use for specs
- How to use reference specs for third-party APIs
- How to separate data model from routing from layout
- How to write tests that catch UI completeness issues, not just route existence
