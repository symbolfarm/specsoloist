---
name: spec_format
type: specification
status: draft
---

# 1. Overview

This document defines the **Spec Format** — the structure for `.spec.md` files used by SpecSoloist and Spechestra. Specs are the source of truth for code generation.

# 2. Philosophy: Requirements, Not Blueprints

Specs define **what** a module must do, not **how** to do it. The agent choosing the implementation is free to make its own design decisions.

**A spec should include:**
- Public API names (class names, function names, method signatures) — these are the interface contract
- Behavior descriptions — what each public function/method does
- Edge cases and error conditions
- Examples with inputs and expected outputs
- Constraints (non-functional requirements)

**A spec should NOT include:**
- Private method names or internal helpers
- Algorithm choices (e.g., "use Kahn's algorithm", "use BFS")
- Internal data structures or field names
- Implementation-level decomposition

**The test for a good spec:** Can a competent developer implement it in any language without seeing the original code, producing functionally equivalent behavior? If the spec prescribes internals, it's just a blueprint — a fancy copy. If it prescribes requirements, it's genuinely useful.

### Example: Good vs. Over-Specified

**Over-specified (avoid):**
```markdown
## _topological_sort(graph) -> list
Implements Kahn's algorithm. Initialize in-degree map, use queue...
```

**Requirements-oriented (preferred):**
```markdown
## resolve_build_order(spec_names) -> list of strings
Compute a linear build order. Dependencies appear before dependents.
When multiple specs have no ordering between them, sort alphabetically
for determinism. Raises CircularDependencyError if a cycle exists.
```

The first dictates implementation. The second defines behavior — the agent picks the algorithm.

### Examples vs. Verification: Different Levels of Specificity

Specs contain two sections that might look similar but serve different purposes:

- **`# Examples`** describes behavior — what happens given certain inputs. Aim for
  language-agnostic prose or tables. "Given a build with specs [config, parser], the
  list displays both names in dependency order." Avoid language-specific test code here.

- **`# Verification`** is a language-specific smoke test compiled to a real test file.
  Import statements, assertions, and framework API calls belong here. This section
  is expected to be tied to the target language.

The distinction matters because `# Examples` communicates requirements to humans and
soloists, while `# Verification` produces executable validation. When example code
starts referencing specific API methods (`app.query_one("Widget").render()`), it has
crossed from requirement into implementation — move it to `# Verification` or rewrite
it as prose.

### Testability as a Constraint

When a module must be testable in specific ways (headless mode, no network access,
no multi-threaded setup required), state this in `# Constraints`. Testability
requirements are real non-functional requirements that affect implementation choices:

```markdown
# Constraints
- Must be testable without a running terminal (headless mode)
- No external service dependencies in unit tests
- State mutations must be observable without threading
```

These constraints prevent surprises where a correct implementation turns out to be
untestable in CI.

# 3. Spec Types

| Type | Purpose | Granularity |
|------|---------|-------------|
| `function` | A single function (full format) | One operation |
| `type` | A data structure/schema (full format) | One type definition |
| `bundle` | Multiple trivial functions/types | Compact format |
| `module` | Aggregates functions/types for export | Composition of specs |
| `workflow` | Execution flow | Steps referencing specs |
| `reference` | Third-party API documentation | One external library |

**When to use which:**
- `bundle`: When the module is a collection of related functions/types where each can be described in a sentence. Most modules should start here.
- `function`/`type`: Only when a single function or type is complex enough to need full Behavior, Constraints, Contract, and Examples sections.
- `module`: When you need to re-export a public API from sub-specs.
- `workflow`: Multi-step execution with data flow between steps.
- `reference`: When documenting a third-party library (FastHTML, Vercel AI SDK, etc.) so soloists have accurate API docs. No code is generated — the spec body is injected as context into dependent soloists' prompts.

# 4. File Structure

```
project/
  src/
    math/
      factorial.spec.md      # type: function
      is_prime.spec.md       # type: function
      mod.spec.md            # type: module (optional, aggregates)
    types/
      user.spec.md           # type: type
    api/
      create_user.spec.md    # type: function
      mod.spec.md            # type: module
    main.spec.md             # type: workflow
```

# 5. Frontmatter

```yaml
---
name: factorial                    # Required: identifier (lowercase, snake_case)
type: function                     # Required: function | type | bundle | module | workflow
status: draft                      # Optional: draft | review | stable (default: draft)
version: 1.0.0                     # Optional: semver
dependencies:                      # Optional: list of specs this depends on
  - types/user
  - math/factorial
tags:                              # Optional: for organization
  - math
  - pure
---
```

**Note:** No `language_target` — that's build configuration, not spec content.

# 6. Sections by Spec Type

## 6.1 Bundle Spec

The most common spec type. Use for a module that contains several related functions and/or types.

```markdown
---
name: manifest
type: bundle
tags:
  - core
  - builds
---

# Overview

Build manifest for tracking spec compilation state. Enables incremental
builds by recording what was built, when, and from what inputs.

# Types

## SpecBuildInfo

Build record for a single spec.

**Fields:** `spec_hash` (string), `built_at` (ISO timestamp string),
`dependencies` (list of strings), `output_files` (list of strings).

Must support round-tripping to/from dict for JSON serialization.

## BuildManifest

Collection of build records, persisted as JSON.

**Methods:**
- `get_spec_info(name)` -> SpecBuildInfo or None
- `update_spec(name, spec_hash, dependencies, output_files)` — record a build
- `save(build_dir)` — persist to disk
- `load(build_dir)` (classmethod) — load or return empty if missing/corrupt

# Functions

## compute_file_hash(path) -> string

SHA-256 hash of a file. Returns empty string if file doesn't exist.

## compute_content_hash(content) -> string

SHA-256 hash of a string.

# Behavior

## Incremental rebuild logic

A spec needs rebuilding if ANY of:
1. Never been built (not in manifest)
2. Content hash changed
3. Dependency list changed
4. Any dependency was rebuilt this cycle

# Examples

| Scenario | needs_rebuild? | Why |
|----------|---------------|-----|
| Spec not in manifest | Yes | Never built |
| Hash changed | Yes | Content changed |
| Deps changed | Yes | Dependencies changed |
| Dep rebuilt this cycle | Yes | Cascade |
| Nothing changed | No | Up to date |
```

**Bundle function fields:**
- `inputs`: Required — input parameters
- `outputs`: Required — output values
- `behavior`: Required — one-line description
- `contract`: Optional — pre/post conditions
- `examples`: Optional — input/output pairs

**References:** Items are referenced as `bundle_name/item_name` (e.g., `math_utils/add`).

## 6.2 Function Spec

For a single complex function that needs full specification.

```markdown
---
name: factorial
type: function
---

# Overview

Computes the factorial of a non-negative integer.

# Interface

```yaml:schema
inputs:
  n:
    type: integer
    minimum: 0
    description: The number to compute factorial of
outputs:
  result:
    type: integer
    minimum: 1
```

# Behavior

- [FR-01]: Return 1 when n is 0
- [FR-02]: Return n * (n-1)! for n > 0

# Constraints

- [NFR-01]: Must be pure (no side effects)
- [NFR-02]: Must handle n up to 20 without overflow

# Contract

- **Pre**: n >= 0
- **Post**: result >= 1

# Examples

| Input | Output | Notes |
|-------|--------|-------|
| 0 | 1 | Base case |
| 5 | 120 | 5! = 120 |
| -1 | Error | Negative input |
```

## 6.3 Type Spec

```markdown
---
name: user
type: type
---

# Overview

Represents a user account in the system.

# Schema

```yaml:schema
properties:
  id:
    type: string
    format: uuid
  email:
    type: string
    format: email
  name:
    type: string
    minLength: 1
    maxLength: 100
  created_at:
    type: datetime
required:
  - id
  - email
```

# Constraints

- [NFR-01]: Email must be unique across all users

# Examples

| Valid | Invalid | Why |
|-------|---------|-----|
| {id: "abc", email: "a@b.com", name: "Jo"} | | Complete |
| | {email: "a@b.com"} | Missing id |
```

## 6.4 Module Spec

For aggregating and re-exporting sub-specs as a public API.

```markdown
---
name: resolver
type: module
tags:
  - core
  - dependencies
---

# Overview

Dependency resolution for multi-spec builds. Builds dependency graphs,
computes build orders, detects cycles, and determines affected specs.

# Exports

- `CircularDependencyError`: Exception for dependency cycles.
- `MissingDependencyError`: Exception for missing dependencies.
- `DependencyGraph`: Graph with methods to query relationships.
- `DependencyResolver`: Main resolver for build order computation.

# DependencyResolver

## Methods

### resolve_build_order(spec_names=None) -> list of strings

Compute a linear build order. Dependencies before dependents.
Alphabetical when no ordering constraint exists.

### get_parallel_build_order(spec_names=None) -> list of lists

Group specs into parallelizable levels.

### get_affected_specs(changed_spec, graph=None) -> list of strings

All transitive dependents of the changed spec, in build order.

# Examples

| Method | Input | Expected |
|--------|-------|----------|
| resolve_build_order | A depends on B | [B, A] |
| get_parallel_build_order | A,B independent; C depends on both | [[A,B], [C]] |
| get_affected_specs("B") | A depends on B | [B, A] |
```

## 6.5 Workflow Spec

```markdown
---
name: process_order
type: workflow
dependencies:
  - validate_order
  - charge_payment
  - send_confirmation
---

# Overview

End-to-end order processing: validate, charge, confirm.

# Interface

```yaml:schema
inputs:
  order:
    type: ref
    ref: types/order
outputs:
  confirmation:
    type: ref
    ref: types/confirmation
```

# Steps

```yaml:steps
- name: validate
  spec: validate_order
  inputs:
    order: inputs.order

- name: charge
  spec: charge_payment
  inputs:
    amount: validate.outputs.total
    payment_method: inputs.order.payment
  checkpoint: true

- name: confirm
  spec: send_confirmation
  inputs:
    order: inputs.order
    transaction_id: charge.outputs.transaction_id
```

# Error Handling

- If `validate` fails: Return validation errors, do not proceed
- If `charge` fails: Retry up to 3 times, then notify admin
```

## 6.6 Reference Spec

For documenting a third-party library's API. No implementation is generated. The spec body is
injected into the prompts of dependent soloists as context, grounding them in the real API.

| Section | Required | Purpose |
|---------|----------|---------|
| `# Overview` | Yes | Library name, package name, version range, import path |
| `# API` | Yes | Functions, types, attributes, gotchas — prose or tables |
| `# Verification` | Recommended | 3–10 lines of import + smoke tests; compiled to `tests/test_{name}.py` |

```markdown
---
name: fasthtml_interface
type: reference
status: stable
---

# Overview

The subset of FastHTML (`python-fasthtml >= 0.12`) used in this project.
Always import from `fasthtml.common`, never from `fasthtml` directly.

# API

## fast_app()

Returns `(app, rt)` — the ASGI app and route decorator factory.

## HTML components

`Div`, `P`, `H1`, `Form`, `Input`, `Button`, `Ul`, `Li` — all share the signature
`Tag(*children, **attrs)`. Use `hx_post`, `hx_swap`, `hx_target` for HTMX attributes.

# Verification

```python
from fasthtml.common import fast_app, serve, Div
app, rt = fast_app()
assert callable(rt)
div = Div("hello", id="x")
assert "hello" in str(div)
```
```

**Key rules:**
- Specs that depend on a reference spec list it in `dependencies:` in their frontmatter.
- Soloists read reference spec bodies as API documentation — they do not import from them.
- If `# Verification` is absent, no test file is generated (a warning is shown, not an error).
- A missing version range in `# Overview` triggers a quality warning.

# 6.7 E2E Test Spec

For end-to-end browser tests (Playwright / pytest-playwright). Use `type: bundle`
with a `# Test Scenarios` table instead of a `# Behavior` section.

**Selector contract:** When a component spec describes interactive elements, include
`data-testid` attributes for each. The E2E spec references them using stable selectors:

```markdown
# In layout.spec.md (component spec)
## `todo_item(text: str, index: int) -> Li`
Returns `<li data-testid="todo-item">` containing:
- A `<button data-testid="delete-btn" hx_delete="/todos/{index}">`

# In e2e_todos.spec.md (test spec)
| Delete todo | Click [data-testid="delete-btn"] | Item removed from list |
```

**Test Scenarios table:** Each row is a complete user journey, not a function call:

```markdown
# Test Scenarios

| Scenario | Steps | Expected |
|----------|-------|----------|
| Add todo | Fill "Buy milk" in input, click Add | "Buy milk" in #todo-list |
| Delete todo | Add "Buy milk", click delete button | Item removed from list |
| Empty add | Click Add with empty input | List unchanged |
```

Soloists translate each row into a `test('...', async ({ page }) => { ... })` block
(TypeScript) or `def test_...(page)` function (pytest-playwright).

**Dev server:** E2E tests need a running server. For Python:
- Use a session-scoped subprocess fixture that starts and polls the server.

For TypeScript/Next.js:
- Use `playwright.config.ts` with `webServer: { command: 'npm run dev', port: 3000 }`.

**Keep E2E tests separate** from unit tests — use a separate arrangement and spec
directory. Run with `sp conduct specs/e2e/ --arrangement arrangement.e2e.yaml`.

See `docs/e2e-testing.md` for the full guide including mocking and CI setup.

# 7. Schema Types

The `yaml:schema` block uses a language-agnostic type system:

## 7.1 Primitive Types

| Type | Description | Constraints |
|------|-------------|-------------|
| `integer` | Whole number | `minimum`, `maximum` |
| `number` | Floating point | `minimum`, `maximum` |
| `string` | Text | `minLength`, `maxLength`, `pattern`, `format` |
| `boolean` | True/false | - |
| `datetime` | ISO 8601 timestamp | - |
| `date` | ISO 8601 date | - |

## 7.2 Compound Types

| Type | Description | Example |
|------|-------------|---------|
| `array` | List of items | `{type: array, items: {type: integer}}` |
| `object` | Key-value map | `{type: object, properties: {...}}` |
| `ref` | Reference to type spec | `{type: ref, ref: types/user}` |
| `enum` | One of fixed values | `{type: string, enum: [a, b, c]}` |
| `union` | One of multiple types | `{type: union, options: [...]}` |
| `optional` | May be absent | `{type: optional, of: {type: string}}` |

## 7.3 String Formats

| Format | Description |
|--------|-------------|
| `email` | Valid email address |
| `uuid` | UUID v4 |
| `uri` | Valid URI |
| `ipv4` | IPv4 address |
| `ipv6` | IPv6 address |

# 8. Section Reference

| Section | Function | Type | Bundle | Module | Workflow | Reference | Required |
|---------|----------|------|--------|--------|----------|-----------|----------|
| Overview | Y | Y | Y | Y | Y | Y | Yes |
| Interface/Schema | Y | Y | - | - | Y | - | Yes* |
| Functions block | - | - | Y | - | - | - | Yes** |
| Types block | - | - | Y | - | - | - | Yes** |
| Behavior | Y | - | - | - | - | - | Yes |
| Steps | - | - | - | - | Y | - | Yes |
| Exports | - | - | - | Y | - | - | Yes |
| API | - | - | - | - | - | Y | Yes |
| Verification | - | - | - | - | - | Y | Recommended |
| Constraints | Y | Y | - | - | - | - | No |
| Contract | Y | - | - | - | - | - | No |
| Examples | Y | Y | Y | Y | - | - | No |
| Error Handling | - | - | - | - | Y | - | No |

*Interface required for function/type/workflow; **At least one of Functions or Types required for bundle.

# 9. Naming Conventions

- **Spec names**: `snake_case` (e.g., `create_user`, `is_prime`)
- **Type names**: `snake_case` (e.g., `user`, `order_item`)
- **Paths**: Forward slash, no extension (e.g., `types/user`, `math/factorial`)
- **Refs in schema**: Full path from src (e.g., `ref: types/user`)

# 10. Compilation

At build time, the Conductor:

1. Reads all specs and builds dependency graph
2. Infers or reads target language from build config
3. Compiles each spec to target language:
   - `function` -> function/method
   - `type` -> class/struct/interface
   - `bundle` -> module with all functions and types
   - `module` -> module/package aggregating exports
   - `workflow` -> executable script/function
   - `reference` -> no implementation; body injected as context into dependent soloists' prompts; `# Verification` compiled to a test file

Build configuration (not in spec):
```yaml
# specsoloist.yaml
build:
  language: python
  output_dir: build/
  test_framework: pytest
```
