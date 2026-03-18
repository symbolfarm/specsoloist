# FastHTML Incremental Adoption (Python)

`examples/fasthtml_incremental/` shows how to introduce SpecSoloist into an **existing**
FastHTML app — without rewriting everything from scratch. It accompanies the
[Incremental Adoption Guide](../incremental-adoption.md).

## The scenario

`original/app.py` is a working priority todo app in a single file — no specs, no agents.
The example walks through extracting specs from it using `sp respec`, validating them,
and running `sp conduct` to generate equivalent code with full test coverage.

## What it demonstrates

- **`sp respec`**: extract requirements from existing code into a spec
- **Spec review**: removing implementation details from generated specs before committing
  them as requirements
- **Round-trip validation**: running generated tests against generated code to confirm
  the specs correctly capture the original contract
- **Gradual coexistence**: the original app and the spec-generated modules can live
  side-by-side during transition

## Spec structure

| Spec | What it covers |
|------|----------------|
| `specs/state.spec.md` | In-memory todo storage — add, delete, filter, stats |
| `specs/layout.spec.md` | FastHTML UI components — badges, rows, forms, pages |
| `specs/routes.spec.md` | HTTP route handlers — GET, POST, DELETE, /stats |

`routes` depends on both `state` and `layout`; the conductor resolves build order
automatically.

## Running it

```bash
cd examples/fasthtml_incremental
uv sync
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
uv run pytest
```

## Full walk-through

See the [Incremental Adoption Guide](../incremental-adoption.md) for the step-by-step
process: audit, respec, validate, round-trip check, and shadow replace.
