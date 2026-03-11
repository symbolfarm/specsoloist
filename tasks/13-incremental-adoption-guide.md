# Task: Incremental Adoption Guide — Adding SpecSoloist to an Existing Project

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.

The current documentation assumes you are starting a new project from scratch. But the most
common real-world scenario is: you have an existing FastHTML or Next.js app with 5–50 files,
and you want to adopt SpecSoloist for new features or to bring existing modules under spec.

This is meaningfully different from greenfield use:
- Existing code has implicit contracts that `sp respec` must extract
- Existing modules import other modules — specs inherit these dependencies
- You can't respec everything at once; you need a safe incremental path
- Generated code must coexist with unspecced code, not replace it wholesale

There is no current documentation for this workflow. This task writes it.

## What to Build

### 1. Guide: `docs/incremental-adoption.md`

A step-by-step guide covering:

**Step 0: Audit your codebase**
- Run `sp init` in the project root (or subdirectory where specs will live)
- Identify which modules are self-contained and have clear public APIs — these are the best
  candidates to respec first (utility functions, data models, API clients)
- Avoid respeccing modules with many external callers until you understand the impact

**Step 1: Respec a leaf module with `sp respec`**
- Choose a module with no local dependencies (a "leaf" in the import graph)
- Run `sp respec src/mymodule.py` — this generates `specs/mymodule.spec.md`
- Review the generated spec: does it describe requirements or implementation details?
  Edit to remove implementation detail (algorithm names, internal helper names)
- Run `sp validate specs/mymodule.spec.md`

**Step 2: Validate the round-trip**
- Run `sp conduct specs/mymodule.spec.md --arrangement arrangement.yaml`
- Run the generated tests against the *original* implementation:
  `PYTHONPATH=src uv run pytest tests/test_mymodule.py`
- If tests pass against the original code, the spec correctly captures the contract
- If tests fail, the spec is wrong — edit and repeat

**Step 3: Coexistence strategy**
Three approaches, in order of risk:

a) **Side-by-side (lowest risk):** Keep `src/mymodule.py` unchanged. Generated code goes to
   `build/mymodule.py`. Run both test suites. Use generated code only when you're confident.

b) **Shadow replacement:** When you're confident in the spec, replace `src/mymodule.py` with
   the generated version. Git history lets you revert.

c) **Spec-only mode:** Delete `src/mymodule.py`, commit only the spec. From now on, `sp conduct`
   is the source. This is the full SpecSoloist model — only safe once you trust the round-trip.

**Step 4: Handling modules with local dependencies**
- When respeccing `src/routes.py` which imports `src/state.py`, respec `state` first
- Add `state` to the `dependencies` field of `routes.spec.md`
- The conductor will compile `state` before `routes` automatically

**Step 5: Reference specs for third-party libraries**
- For any import of an obscure/versioned library, write a `reference` spec before respeccing
  the module that uses it (see task 04)
- Common candidates: custom API clients, new ORMs, niche UI libraries

**Step 6: Partial adoption in a large codebase**
- Not all files need specs — SpecSoloist works well as a spec layer for *new* features
  added to an existing unspecced codebase
- Use a `specs/` subdirectory and arrangement that outputs to `src/features/` rather than
  overwriting existing code
- Document which parts of the codebase are spec-driven vs maintained manually

### 2. `sp respec` improvements (if gaps are found)

While writing the guide, test `sp respec` on actual FastHTML and Next.js code. If the
generated specs are over-specified (contain private method names, algorithm details), note
this and open a follow-up issue. If `sp respec` fails on certain file patterns, document
the workaround.

Do not fix `sp respec` bugs in this task unless they are trivial — just document and flag.

### 3. FastHTML incremental adoption example

Create `examples/fasthtml_incremental/` as a companion to `examples/fasthtml_app/`:
- `original/app.py` — a complete FastHTML app written without SpecSoloist (3–4 routes,
  in-memory state, form handling)
- `specs/` — the specs extracted by `sp respec` + hand-reviewed
- `arrangement.yaml` — matching the FastHTML template from task 08
- `README.md` — walkthrough of the incremental adoption steps above using this example

The `original/app.py` should be a slightly richer version of the todo app: todos with
priorities (low/medium/high), a filter route (`GET /todos?priority=high`), and a simple
statistics endpoint (`GET /stats` returning count per priority). This gives `sp respec`
enough surface area to be interesting.

### 4. Update `README.md`

Add a short "Adding SpecSoloist to an existing project" section with a link to the guide.

## Files to Read First

- `src/specsoloist/respec.py` — current `sp respec` implementation
- `.claude/agents/respec.md` — respec agent instructions
- `examples/fasthtml_app/` — existing validated example to reference
- `README.md` — to understand current documentation structure
- `AGENTS.md`

## Success Criteria

1. `docs/incremental-adoption.md` exists and covers all 6 steps above.
2. `examples/fasthtml_incremental/original/app.py` is a working FastHTML app.
3. `examples/fasthtml_incremental/specs/` contains specs extracted from it.
4. `sp conduct examples/fasthtml_incremental/specs/ --arrangement ...` produces passing tests.
5. `examples/fasthtml_incremental/README.md` walks through the adoption steps.
6. `README.md` links to the guide.
7. No regressions to `sp respec` — `uv run python -m pytest tests/` still passes.

## Notes

The key insight to communicate in the guide: you don't have to go "full SpecSoloist" all at
once. The spec layer and the hand-written layer can coexist indefinitely. The value of specs
accumulates even when only 20% of the codebase is specced — those 20% are documented,
testable, and regenerable.
