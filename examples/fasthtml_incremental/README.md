# FastHTML Incremental Adoption Example

This example shows how to add SpecSoloist to an existing FastHTML app — without rewriting
everything from scratch. It accompanies the [Incremental Adoption Guide](../../docs/incremental-adoption.md).

The "before" state is `original/app.py`: a working priority todo app with no specs. The
"after" state is `specs/` — three hand-reviewed specs extracted from the original code.

---

## The Original App

`original/app.py` is a self-contained FastHTML app with:

- In-memory todo storage with priorities: `low`, `medium`, `high`
- `GET /` — home page with optional `?priority=` filter
- `POST /todos` — add a todo (text + priority)
- `DELETE /todos/{index}` — remove a todo
- `GET /stats` — count of todos per priority

Run it directly:

```bash
cd examples/fasthtml_incremental
uv sync
uv run python original/app.py
```

---

## The Adoption Walk-Through

### Step 0: Audit

The original app has three logical layers, all in one file:

- **State** — in-memory `todos` list; `PRIORITIES` constant; add/delete/filter/stats logic
- **Layout** — FastHTML component functions (`priority_badge`, `todo_item_row`, etc.)
- **Routes** — HTTP handlers (`get`, `post`, `delete`, `stats`)

State has no local dependencies — the right place to start. Layout uses state types but no
state functions. Routes depend on both.

### Step 1: Respec the leaf module

```bash
sp respec original/app.py
```

`sp respec` extracts all three layers from the single-file app into a single spec. Since we
want separate specs for testability, we split the output manually into:

- `specs/state.spec.md`
- `specs/layout.spec.md`
- `specs/routes.spec.md`

For a real multi-file project, run `sp respec` on each file separately.

The generated specs were reviewed to remove implementation details:

- Removed mention of the internal `todos` list name
- Removed Python-specific implementation notes
- Confirmed that public function names, signatures, and behaviour are accurately described

### Step 2: Validate

```bash
sp validate specs/state.spec.md
sp validate specs/layout.spec.md
sp validate specs/routes.spec.md
```

All three should report `VALID`. Fix any errors before continuing.

### Step 3: Round-trip check

Generate code and tests from the specs, then run the generated tests against the original app:

```bash
sp conduct specs/ --arrangement arrangement.yaml
# generates src/state.py, src/layout.py, src/routes.py
# generates tests/test_state.py, tests/test_layout.py, tests/test_routes.py

PYTHONPATH=src uv run pytest tests/
```

If tests pass against the generated code, the specs correctly capture the contract.

### Step 4: Dependency chain

`routes.spec.md` declares:

```yaml
dependencies:
  - state
  - layout
```

The conductor resolves this order automatically. `state` and `layout` compile before `routes`.

---

## The Specs

| Spec | What it covers |
|------|----------------|
| `specs/state.spec.md` | In-memory todo storage — add, delete, filter, stats |
| `specs/layout.spec.md` | FastHTML UI components — badges, rows, forms, pages |
| `specs/routes.spec.md` | HTTP route handlers — GET, POST, DELETE, /stats |

---

## Build from Specs

```bash
cd examples/fasthtml_incremental
uv sync

# Build all three specs in dependency order
sp conduct specs/ --arrangement arrangement.yaml

# Run generated tests
uv run pytest
```

The arrangement outputs generated code to `src/` and tests to `tests/`. These directories are
gitignored — only the specs, arrangement, and original app are committed.

---

## Next Steps

Once you trust the round-trip:

1. **Shadow replace** — swap `original/app.py` logic with the generated `src/` modules
2. **Spec-only mode** — delete `original/app.py`, treat specs as the only source of truth
3. **Add features** — write a new spec for the feature, `sp conduct` it, integrate

See the [Incremental Adoption Guide](../../docs/incremental-adoption.md) for the full coexistence
strategy discussion.
