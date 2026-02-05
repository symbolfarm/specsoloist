---
name: spec_format
type: specification
status: draft
---

# 1. Overview

This document defines the **Spec Format** - the structure for `.spec.md` files used by SpecSoloist and Spechestra. The format is designed to be:

- **Language-agnostic**: Specs describe *what*, not *how* in any particular language
- **Granular**: One concept per spec (function, type, module)
- **Composable**: Specs can depend on and reference other specs
- **Human-readable**: Markdown with structured YAML blocks

# 2. Spec Types

| Type | Purpose | Granularity |
|------|---------|-------------|
| `function` | A single function (full format) | One operation |
| `type` | A data structure/schema (full format) | One type definition |
| `bundle` | Multiple trivial functions/types | Compact format |
| `module` | Aggregates functions/types for export | Composition of specs |
| `workflow` | Execution flow | Steps referencing specs |

**When to use which:**
- `function`/`type`: Complex specs needing full sections (Behavior, Constraints, Contract, Examples)
- `bundle`: Related trivial helpers where a one-liner `behavior:` suffices
- `module`: Re-exporting a public API surface
- `workflow`: Multi-step execution with data flow

# 3. File Structure

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

# 4. Frontmatter

```yaml
---
name: factorial                    # Required: identifier (lowercase, snake_case)
type: function                     # Required: function | type | module | workflow
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

**Note:** No `language_target` - that's build configuration, not spec content.

# 5. Sections by Spec Type

## 5.1 Function Spec

```markdown
---
name: factorial
type: function
---

# Overview
[1-2 sentences: what this function does]

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
- [FR-02]: Return n × factorial(n-1) for n > 0

# Constraints
- [NFR-01]: Must be pure (no side effects)
- [NFR-02]: Must handle n up to 20 without overflow

# Contract
- **Pre**: n >= 0
- **Post**: result >= 1
- **Invariant**: factorial(n) = n! (mathematical definition)

# Examples
| Input | Output | Notes |
|-------|--------|-------|
| 0 | 1 | Base case |
| 5 | 120 | 5! = 120 |
| -1 | Error | Negative input |
```

## 5.2 Type Spec

```markdown
---
name: user
type: type
---

# Overview
[1-2 sentences: what this type represents]

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
- [NFR-02]: ID must be immutable after creation

# Examples
| Valid | Invalid | Why |
|-------|---------|-----|
| {id: "abc", email: "a@b.com", name: "Jo"} | | Complete |
| | {email: "a@b.com"} | Missing id |
```

## 5.3 Bundle Spec

For related trivial functions and types that don't need full specifications.

```markdown
---
name: math_utils
type: bundle
tags:
  - math
  - utils
---

# Overview
Common mathematical utility functions.

# Functions
```yaml:functions
add:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: Return a + b

subtract:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: Return a - b

clamp:
  inputs:
    value: {type: number}
    min: {type: number}
    max: {type: number}
  outputs: {result: number}
  behavior: Return value constrained to [min, max]
  contract:
    pre: min <= max
```

# Types
```yaml:types
point_2d:
  properties:
    x: {type: number}
    y: {type: number}
  required: [x, y]
```
```

**Bundle function fields:**
- `inputs`: Required - input parameters
- `outputs`: Required - output values
- `behavior`: Required - one-line description
- `contract`: Optional - pre/post conditions
- `examples`: Optional - input/output pairs

**References:** Individual items are referenced as `bundle_name/item_name` (e.g., `math_utils/add`).

## 5.4 Module Spec

```markdown
---
name: math
type: module
dependencies:
  - math/factorial
  - math/is_prime
  - math/fibonacci
---

# Overview
[1-2 sentences: what this module provides]

# Exports
- `factorial`: Compute factorial of n
- `is_prime`: Check if n is prime
- `fibonacci`: Compute nth Fibonacci number

# Usage
[Optional: example of how the module is used as a whole]
```

## 5.5 Workflow Spec

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
[1-2 sentences: what this workflow accomplishes]

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
  checkpoint: true    # Pause for approval

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

# 6. Schema Types

The `yaml:schema` block uses a language-agnostic type system:

## 6.1 Primitive Types

| Type | Description | Constraints |
|------|-------------|-------------|
| `integer` | Whole number | `minimum`, `maximum` |
| `number` | Floating point | `minimum`, `maximum` |
| `string` | Text | `minLength`, `maxLength`, `pattern`, `format` |
| `boolean` | True/false | - |
| `datetime` | ISO 8601 timestamp | - |
| `date` | ISO 8601 date | - |

## 6.2 Compound Types

| Type | Description | Example |
|------|-------------|---------|
| `array` | List of items | `{type: array, items: {type: integer}}` |
| `object` | Key-value map | `{type: object, properties: {...}}` |
| `ref` | Reference to type spec | `{type: ref, ref: types/user}` |
| `enum` | One of fixed values | `{type: string, enum: [a, b, c]}` |
| `union` | One of multiple types | `{type: union, options: [...]}` |
| `optional` | May be absent | `{type: optional, of: {type: string}}` |

## 6.3 String Formats

| Format | Description |
|--------|-------------|
| `email` | Valid email address |
| `uuid` | UUID v4 |
| `uri` | Valid URI |
| `ipv4` | IPv4 address |
| `ipv6` | IPv6 address |

# 7. Section Reference

| Section | Function | Type | Bundle | Module | Workflow | Required |
|---------|----------|------|--------|--------|----------|----------|
| Overview | ✓ | ✓ | ✓ | ✓ | ✓ | Yes |
| Interface/Schema | ✓ | ✓ | - | - | ✓ | Yes* |
| Functions block | - | - | ✓ | - | - | Yes** |
| Types block | - | - | ✓ | - | - | Yes** |
| Behavior | ✓ | - | - | - | - | Yes |
| Steps | - | - | - | - | ✓ | Yes |
| Exports | - | - | - | ✓ | - | Yes |
| Constraints | ✓ | ✓ | - | - | - | No |
| Contract | ✓ | - | - | - | - | No |
| Examples | ✓ | ✓ | - | - | - | No |
| Error Handling | - | - | - | - | ✓ | No |

*Interface required for function/type/workflow; **At least one of Functions or Types required for bundle.

# 8. Naming Conventions

- **Spec names**: `snake_case` (e.g., `create_user`, `is_prime`)
- **Type names**: `snake_case` (e.g., `user`, `order_item`)
- **Paths**: Forward slash, no extension (e.g., `types/user`, `math/factorial`)
- **Refs in schema**: Full path from src (e.g., `ref: types/user`)

# 9. Compilation

At build time, the SpecConductor:

1. Reads all specs and builds dependency graph
2. Infers or reads target language from build config
3. Compiles each spec to target language:
   - `function` → function/method in target language
   - `type` → class/struct/interface in target language
   - `module` → module/package aggregating exports
   - `workflow` → executable script/function

Build configuration (not in spec):
```yaml
# specsoloist.yaml
build:
  language: python          # or: typescript, go, rust
  output_dir: build/
  test_framework: pytest    # or: jest, go test
```

# 10. Migration from Current Format

| Current | New |
|---------|-----|
| `language_target: python` in frontmatter | Move to `specsoloist.yaml` |
| Multiple functions in one spec | Split into separate function specs |
| `### function(args) -> return` | Use `yaml:schema` block |
| `type: module` with functions | `type: module` with exports + separate function specs |
| Test Scenarios table | Examples section |
