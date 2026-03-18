# Spec Types

Specs are Markdown files with a YAML frontmatter block. The `type` field controls which
sections are required, how the parser validates the spec, and what code (if any) the
compiler generates.

## Quick Reference

| Type | Use when | Generates |
|------|----------|-----------|
| `bundle` | A module with several related functions/types | Implementation + tests |
| `function` | A single complex function needing full specification | Implementation + tests |
| `type` | A data structure or schema | Type definition + tests |
| `module` | Aggregating sub-specs into a single public API | Re-exports |
| `workflow` | A multi-step execution pipeline | Runner script |
| `reference` | Documenting a third-party library | Verification tests only |

When in doubt, start with `bundle`. It handles the vast majority of modules and is the
most flexible type.

---

## `bundle`

The default type. Use it for any module that groups related functions and/or types. Each
item in a bundle has a one-line `behavior` field rather than a full spec section.

**Key sections:** `# Overview`, `# Types` (optional), `# Functions`, `# Behavior`,
`# Examples`

**Bundle function fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `inputs` | Yes | Named parameters with types |
| `outputs` | Yes | Return type(s) |
| `behavior` | Yes | One-line description |
| `contract` | No | Pre/post conditions |

**Example** — `score/manifest.spec.md`, SpecSoloist's own build manifest:

```markdown
--8<-- "score/manifest.spec.md"
```

---

## `function`

For a single function complex enough to warrant its own Behavior, Constraints, Contract,
and Test Scenarios sections. If you find yourself writing a bundle with one item, use
`function` instead.

**Key sections:** `# Overview`, `# Interface` (yaml:schema), `# Behavior`,
`# Constraints`, `# Contract`, `# Test Scenarios`

**Example** — `examples/math/factorial.spec.md`:

```markdown
--8<-- "examples/math/factorial.spec.md"
```

---

## `type`

For a data structure or schema. No functions — just the shape of the data, its
constraints, and examples of valid/invalid values. The compiler generates a type
definition (dataclass, Pydantic model, TypeScript interface, etc.).

**Key sections:** `# Overview`, `# Schema` (yaml:schema), `# Constraints`, `# Examples`

**Example** — `examples/math/user.spec.md`:

```markdown
--8<-- "examples/math/user.spec.md"
```

---

## `module`

Aggregates exports from sub-specs into a single public API surface. A module spec lists
what it re-exports and documents high-level behaviour — it doesn't re-specify what
sub-specs already cover. Use it when you want a single import point for consumers of a
package.

**Key sections:** `# Overview`, `# Exports` (list of re-exported names), method/class
docs that add module-level context.

**Example** — `score/resolver.spec.md`, SpecSoloist's own dependency resolver (excerpt):

```markdown
---
name: resolver
type: module
tags:
  - core
  - dependencies
---

# Overview

Dependency resolution for multi-spec builds. Given a set of specs that declare
dependencies on each other, this module can:

- Build a dependency graph
- Compute a valid build order (dependencies before dependents)
- Group specs into parallelizable levels
- Determine which specs are affected when one changes
- Detect and report circular dependencies and missing dependencies

# Exports

- `CircularDependencyError`: Exception raised when specs form a dependency cycle.
- `MissingDependencyError`: Exception raised when a spec depends on one that doesn't exist.
- `DependencyGraph`: A dependency graph with methods to query relationships.
- `DependencyResolver`: The main resolver that builds graphs and computes build orders.

# Error Types

## CircularDependencyError

An exception with a `cycle` attribute (list of spec names forming the cycle).

## MissingDependencyError

An exception with `spec` and `missing` attributes. `spec` is the name of the spec that
declared the dependency; `missing` is the name of the dependency that doesn't exist.

# DependencyResolver

## resolve_build_order(spec_names=None) -> list of strings

Compute a linear build order. Dependencies appear before dependents.
Alphabetical when no ordering constraint exists.
Raises `CircularDependencyError` if a cycle exists.

## get_parallel_build_order(spec_names=None) -> list of lists

Group specs into parallelizable levels. Each level can be compiled concurrently —
all dependencies of specs in level N are in levels 0..N-1.

# Examples

| Method | Input | Expected |
|--------|-------|----------|
| resolve_build_order | A depends on B | `["b", "a"]` |
| get_parallel_build_order | A,B independent; C depends on both | `[["a","b"], ["c"]]` |
```

---

## `workflow`

For multi-step execution where data flows from one step to the next. Workflows reference
other specs by name and wire outputs to inputs. The compiler generates an executable
runner (Python function, JS module, etc.) that calls each step in order.

Workflows are for your **target project** — for example, an order processing pipeline
that validates, then charges, then confirms. SpecSoloist's own orchestration (the
conductor agent that runs `sp conduct`) is separate from this.

**Key sections:** `# Overview`, `# Interface` (yaml:schema), `# Steps` (yaml:steps),
`# Error Handling`

**yaml:steps fields:**

| Field | Description |
|-------|-------------|
| `name` | Step identifier, used to reference its outputs downstream |
| `spec` | The spec to invoke |
| `inputs` | Map of input names to values: `inputs.x` or `prev_step.outputs.y` |
| `checkpoint` | If `true`, the workflow can resume from this step after a failure |

**Example** — `examples/math/math_workflow.spec.md`:

```markdown
--8<-- "examples/math/math_workflow.spec.md"
```

---

## `reference`

For documenting a third-party library. **No implementation is generated.** The spec body
is injected into the prompts of dependent soloists as API documentation, grounding them
in the real library API so they don't hallucinate method signatures or import paths.

### When to use

Any time your project uses a library that is new enough (or niche enough) that LLMs may
not have accurate knowledge of its API. FastHTML, Vercel AI SDK, and similar newer
frameworks are good candidates.

### Required sections

| Section | Required | Purpose |
|---------|----------|---------|
| `# Overview` | Yes | Library name, package, version range, correct import path |
| `# API` | Yes | Functions, classes, and attributes your project actually uses |
| `# Verification` | Recommended | 3–10 lines compiled into `tests/test_{name}.py` |

### Conventions

- **Version range in `# Overview`**: Be explicit about which version the spec documents
  and note any breaking changes between versions. A missing version range triggers a
  quality warning from `sp validate`.
- **Imports and gotchas first**: Put the canonical import statement near the top. For
  libraries with common footguns (wrong module path, deprecated entry points), call them
  out explicitly.
- **Verification makes it living docs**: The `# Verification` section compiles to a test
  file. CI fails if the library API drifts, turning the spec into verified documentation
  rather than a comment that goes stale.
- **Only document what you use**: Reference specs aren't comprehensive library docs —
  they document the subset of the library that your project's soloists will call.

### Dependency wiring

Specs that use the library declare the reference spec in their `dependencies:` frontmatter.
The conductor injects the reference spec body into those soloists' prompts automatically:

```yaml
---
name: routes
type: bundle
dependencies:
  - fasthtml_interface  # reference spec — injected as context, not imported
  - state
---
```

**Example** — `examples/fasthtml_app/specs/fasthtml_interface.spec.md`:

```markdown
--8<-- "examples/fasthtml_app/specs/fasthtml_interface.spec.md"
```
