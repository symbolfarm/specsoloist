# Incremental Adoption: Adding SpecSoloist to an Existing Project

SpecSoloist works well for greenfield projects, but the most common real-world scenario is
different: you have an existing FastHTML or Next.js app with 5–50 files, and you want to bring
some of it under spec — without rewriting everything at once.

This guide covers that path. The key insight: **you don't have to go full SpecSoloist all at
once.** The spec layer and the hand-written layer can coexist indefinitely. Even 20% spec
coverage delivers value — those modules are documented, testable, and regenerable.

See `examples/fasthtml_incremental/` for a concrete walkthrough alongside this guide.

---

## Step 0: Audit your codebase

Before touching any files, understand your import graph.

```bash
sp init                              # create arrangement.yaml in the project root
sp init --template python-fasthtml   # or use a template for your stack
```

Identify which modules are good first candidates for `sp respec`:

- **Best candidates:** utility functions, data models, API clients — modules with clear public
  APIs and no local imports.
- **Defer:** modules with many external callers, or modules that import several other local
  modules. Respec the dependencies first.

A module at the bottom of your import graph (a "leaf") is always the right place to start.

---

## Step 1: Respec a leaf module with `sp respec`

Choose the leaf module. Run `sp respec` on it:

```bash
sp respec src/state.py
# writes specs/state.spec.md
```

Open the generated spec and review it critically. The most common issue is **over-specification**:
the spec describes *how* the code works rather than *what* it should do. Signs of this:

- Private function names appear in the spec (`_normalize_priority`, `_todo_store`)
- Algorithm choices appear ("uses a list internally")
- Internal field names appear that callers don't see

Edit these out. A spec should answer: *"Could a competent developer implement this from scratch
using only this spec?"* If yes, it's good. The implementation details are irrelevant.

Then validate:

```bash
sp validate specs/state.spec.md
```

Fix any validation errors before continuing.

---

## Step 2: Validate the round-trip

Run `sp conduct` to generate code and tests from the spec:

```bash
sp conduct specs/state.spec.md --arrangement arrangement.yaml
# writes src/state_generated.py and tests/test_state.py (adjust paths in arrangement)
```

Now run the generated tests against the **original** implementation (not the generated one):

```bash
PYTHONPATH=src uv run pytest tests/test_state.py
```

If the tests pass against the original code, the spec correctly captures the contract. The
spec is a faithful description of what your existing code does.

If tests fail: the spec is wrong, not the code. Edit the spec to match what the code actually
does, then repeat. Common fixes:

- An edge case you forgot to specify (empty input, None, out-of-range index)
- A return type that's more specific than the spec says
- A function signature that differs from what you wrote in the spec

This loop — respec, validate, generate tests, test against original — is the core of incremental
adoption. It builds confidence before you commit to the spec as source of truth.

---

## Step 3: Choose a coexistence strategy

Once tests pass against the original, choose how you want to integrate:

### a) Side-by-side (lowest risk)

Keep `src/state.py` unchanged. Point the arrangement's output path to `src/state_generated.py`
or `build/state.py`. Run both test suites.

Use this when you're not yet confident in the round-trip, or when the module is critical and
you can't afford downtime.

### b) Shadow replacement

When you're confident in the spec, swap `src/state.py` with the generated version. The spec
becomes the new source of truth for future changes.

```bash
cp build/state.py src/state.py
git commit -m "feat: replace state.py with spec-generated version"
```

Git history gives you a safety net if you need to revert.

### c) Spec-only mode

Delete `src/state.py`. Commit only the spec. From now on, `sp conduct` regenerates `src/state.py`
from `specs/state.spec.md`. This is the full SpecSoloist model — treat code as a build artifact.

Only adopt this once you trust the round-trip completely and have a CI job that runs `sp conduct`
before running tests.

---

## Step 4: Handling modules with local dependencies

When you're ready to respec a module that imports other local modules, respec the dependencies first.

For example, `routes.py` imports `state.py`. The adoption order:

1. Respec `state.py` → `specs/state.spec.md` (no local dependencies)
2. Respec `layout.py` → `specs/layout.spec.md` (no local dependencies)
3. Respec `routes.py` → `specs/routes.spec.md`

Then add the `dependencies` field to `routes.spec.md`:

```markdown
---
name: routes
type: bundle
dependencies:
  - state
  - layout
---
```

The conductor resolves these automatically and compiles `state` and `layout` before `routes`.

---

## Step 5: Reference specs for third-party libraries

If a module uses an obscure or versioned library that LLMs may hallucinate (FastHTML, a custom
ORM, an internal SDK), write a `type: reference` spec before respeccing modules that depend on it.

```bash
# Check existing reference specs first
ls specs/
# If none exists for your library, create one:
sp create fasthtml_interface --type reference
```

A reference spec documents only the subset of the library your project actually uses. Every
spec that depends on it lists it in `dependencies:`. The conductor injects the reference spec
into each soloist's context.

See the [database patterns guide](database-patterns.md) for the full reference spec pattern, and
`examples/fasthtml_app/specs/fasthtml_interface.spec.md` for a concrete example.

---

## Step 6: Partial adoption in a large codebase

In a large app, you don't have to spec every file. SpecSoloist works well as a spec layer for
*new features* added to an existing unspecced codebase:

- Put specs in `specs/` and point the arrangement output to `src/features/` rather than
  overwriting existing files.
- Only new features go through the spec→conduct→test pipeline. Existing code stays as-is.
- As you touch old modules for new features, add a spec then (opportunistic adoption).

It also helps to document which parts of the codebase are spec-driven:

```
src/
  features/          ← generated from specs/, do not edit by hand
    analytics.py
    recommendations.py
  core/              ← hand-written, not yet specced
    auth.py
    database.py
specs/
  analytics.spec.md
  recommendations.spec.md
```

A comment at the top of generated files (`# Generated from specs/analytics.spec.md`) makes
this boundary obvious to contributors.

---

## Testing `sp respec` on your own code

Run `sp respec` and check the quality of what it produces. Common issues and fixes:

| Issue | Symptom | Fix |
|-------|---------|-----|
| Over-specification | Private names, algorithm details in spec | Edit spec; remove internals |
| Missing edge cases | Generated tests fail on original code | Add examples/edge cases to spec |
| Wrong return types | Type mismatch in generated tests | Correct the return type in spec |
| Dependency not declared | Soloist imports something not in context | Add to `dependencies:` |

If `sp respec` consistently produces over-specified output, open a note in `IMPROVEMENTS.md` —
but don't block adoption on it. Hand-edit the spec; that's expected.

---

## Quick reference

```bash
sp respec src/mymodule.py                              # generate spec from code
sp validate specs/mymodule.spec.md                    # check spec structure
sp conduct specs/mymodule.spec.md --arrangement ...   # generate code + tests from spec
PYTHONPATH=src uv run pytest tests/test_mymodule.py  # test original code against spec
sp conduct specs/                                     # build full spec directory
```
