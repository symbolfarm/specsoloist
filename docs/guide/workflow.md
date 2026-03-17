# The SpecSoloist Workflow

Using SpecSoloist requires a shift in mindset: **You are no longer a Coder; you are an Architect.**

Instead of writing logic, you define constraints and behaviors. This guide outlines the recommended workflow for building scalable systems.

## 0. Starting a New Project

The fastest path from idea to working code is `sp vibe`:

```bash
sp vibe "A todo app with user auth and REST API" --template python-fasthtml
```

This runs two steps in sequence:

1. **`sp compose`** — A composer agent drafts architecture and writes `.spec.md` files to `src/`
2. **`sp conduct`** — A conductor agent reads all specs, resolves dependencies, and spawns soloist agents to implement each one

Add `--pause-for-review` to inspect and edit the generated specs before the build starts:

```bash
sp vibe "A todo app with user auth" --pause-for-review
# → drafts specs, pauses
# → you edit src/*.spec.md
# → press Enter to continue building
```

Use `--resume` to treat a new brief as an addendum to an existing project (skips already-compiled specs):

```bash
sp vibe "Add email notifications" --resume
```

---

## 1. The "Leaves-Up" Strategy

For projects you build manually spec-by-spec, build from the bottom up.

1. **Domain First**: Start by defining your data structures (Type Specs). This creates the "vocabulary" for your system.
2. **Dependencies Second**: Build utility modules and helpers that depend on those types.
3. **Core Logic Third**: Build the business logic that uses the utilities.
4. **API/UI Last**: Build the interface layer.

### Example Order

1. `types.spec.md` (User, Order structs)
2. `validation.spec.md` (Input checkers)
3. `order_service.spec.md` (Business logic)

`sp conduct` automates this ordering: it reads the `dependencies:` frontmatter in each spec and compiles in topological order.

---

## 2. The Iteration Loop

Once a component exists, you enter the daily development loop. You rarely touch generated code directly.

### Scenario A: Adding a Feature

1. Open `auth.spec.md`.
2. Add a new function signature to **Interface Specification**.
3. Add a **Functional Requirement** (e.g., `FR-05: The system shall hash passwords using bcrypt`).
4. Run `sp compile auth`.
5. Run `sp test auth`. (SpecSoloist generates new tests for the new requirements.)

### Scenario B: Fixing a Bug

1. You run `sp test` and see a failure.
2. **Do not edit the code.**
3. Run `sp fix auth`.
4. The agent analyzes the failure, reads the spec, and patches the code.
5. *If it fails repeatedly:* Your spec is likely ambiguous. **Refine the spec** (e.g., add a constraint or clarify an edge case).

### Scenario C: Checking for Drift

After making spec changes, verify that the compiled code still matches:

```bash
sp diff auth
```

Reports `MISSING` (spec defines, code lacks), `UNDOCUMENTED` (code has, spec lacks), and `TEST_GAP` (spec defines, no test covers it).

---

## 3. Incremental Builds

For large projects with many specs, avoid recompiling everything from scratch:

```bash
# Resume: skip specs whose output files match the manifest
sp conduct --resume

# Force: recompile everything regardless of manifest state
sp conduct --force
```

`--resume` is the right default for daily development. `--force` is useful after upgrading the framework or changing the arrangement.

---

## 4. The Hybrid Reality

For large projects, you don't have to use SpecSoloist for 100% of the code.

- **SpecSoloist**: Use it for "pure" logic, data models, complex algorithms, and utilities.
- **Hand-Written**: Use manual code for "glue," framework boilerplate (like FastHTML setup or React routing), or highly visual UI components.

SpecSoloist generates standard Python/TypeScript files in your configured output directory. You can import them into your hand-written `main.py` just like any other library.

!!! warning "Do not edit build artifacts"
    If you manually edit a generated file, SpecSoloist will overwrite your changes the next time you compile. If you need manual control, move the file out of the build directory and stop managing it with SpecSoloist.

---

## 5. Best Practices

- **NFRs are your Friend**: If the code works but is "bad" (slow, messy), add a **Non-Functional Requirement**.
    - *Bad*: "Make it fast."
    - *Good*: "NFR-Performance: Must use binary search, O(log n)."
- **Explicit Dependencies**: Ensure your `dependencies: []` list in the spec frontmatter is accurate. This tells the LLM exactly what other modules it can import.
- **Check status before a build**: `sp status` shows which specs are compiled, stale, or missing — useful before running `sp conduct --resume`.
- **Verify before committing**: `sp verify` checks all specs for orchestration readiness (valid dependencies, recognised types) without touching any code.
