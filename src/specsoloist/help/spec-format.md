# Spec Format Reference

Specs are `.spec.md` files that describe *what* code should do. Agents compile them
into implementation files and tests. Specs are language-agnostic — the arrangement
determines the target language.

---

## Frontmatter

```yaml
---
name: factorial          # required: snake_case identifier
type: bundle             # required: bundle | function | type | module | workflow | reference
status: draft            # optional: draft | review | stable
dependencies:            # optional: list of spec names this spec depends on
  - types/user
  - math/utils
tags:                    # optional: for organization
  - math
---
```

---

## Spec types

| Type | Use when |
|------|----------|
| `bundle` | A module with several related functions/types (most common) |
| `function` | A single complex function needing full Behavior + Contract sections |
| `type` | A data structure or schema |
| `module` | Aggregates exports from sub-specs into a public API |
| `workflow` | Multi-step execution with data flowing between steps |
| `reference` | Documents a third-party library; no code generated, body injected into dependent soloists' prompts |

---

## Bundle spec (most common)

```markdown
---
name: manifest
type: bundle
---

# Overview

One paragraph describing what this module does and why it exists.

# Functions

## compute_file_hash(path) -> str

SHA-256 hash of a file at `path`. Returns empty string if file does not exist.

## compute_content_hash(content) -> str

SHA-256 hash of a string.

# Types

## BuildRecord

Tracks one compiled spec. Fields: `spec_hash` (str), `built_at` (ISO str),
`output_files` (list[str]).

# Test Scenarios

| Scenario | Input | Expected |
|----------|-------|----------|
| Existing file | path to a real file | 64-char hex string |
| Missing file | path that does not exist | "" |
| Hash is deterministic | same content twice | identical hashes |
```

Or use a `yaml:test_scenarios` block instead of a Markdown table:

```yaml:test_scenarios
- description: "existing file"
  inputs: {path: "/tmp/test.txt"}
  expected_output: "64-char hex string"
- description: "missing file"
  inputs: {path: "/does/not/exist"}
  expected_output: ""
```

---

## Function spec

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
outputs:
  result:
    type: integer
    minimum: 1
```

# Behavior

- Returns 1 when n is 0
- Returns n * factorial(n-1) for n > 0
- Raises ValueError for negative n

# Contract

- Pre: n >= 0
- Post: result >= 1

# Test Scenarios

| n | result |
|---|--------|
| 0 | 1 |
| 5 | 120 |
| -1 | error |
```

---

## Reference spec

No code is generated. The spec body is injected into the prompts of every dependent
soloist as API documentation.

```markdown
---
name: fasthtml_interface
type: reference
dependencies: []
---

# Overview

FastHTML (`python-fasthtml >= 0.12`). Always import from `fasthtml.common`.

# API

## fast_app()

Returns `(app, rt)` — ASGI app and route decorator.

## Components

`Div`, `P`, `H1`, `Form`, `Input`, `Button` — all use `Tag(*children, **attrs)`.
HTMX: `hx_post`, `hx_swap`, `hx_target`.

# Verification

```python
from fasthtml.common import fast_app, Div
app, rt = fast_app()
assert callable(rt)
```
```

Dependent specs list `fasthtml_interface` in their `dependencies:` frontmatter field.

---

## What belongs in a spec

**Include:**
- Public function/method names and signatures (these are the interface contract)
- Behavior: what each function does, including edge cases and errors
- Test scenarios: concrete inputs and expected outputs

**Do not include:**
- Private method names or internal helpers
- Algorithm choices (e.g. "use Kahn's algorithm")
- Internal data structures
- Language-specific details — those go in `arrangement.yaml`

---

## See also

- `sp help arrangement` — arrangement.yaml reference
- `sp help conduct` — running builds
- `sp validate <name>` — check a spec for quality issues
