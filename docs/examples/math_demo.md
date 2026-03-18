# Math Examples (Python)

The `examples/math/` directory contains a collection of standalone Python specs that
together demonstrate all six spec types. Nothing about the maths is special — these
examples exist to show what each spec type looks like in practice.

## Spec inventory

| File | Type | What it shows |
|------|------|--------------|
| `math_utils.spec.md` | `bundle` | A compact module of related arithmetic functions |
| `factorial.spec.md` | `function` | A single operation with full Behavior/Contract/Tests |
| `user.spec.md` | `type` | A data schema with constraints and valid/invalid examples |
| `math_demo.spec.md` | `module` | Re-exporting factorial and is_prime under one API |
| `math_workflow.spec.md` | `workflow` | A two-step pipeline: compute factorial → check if prime |
| `is_prime.spec.md` | `function` | A second standalone function (dependency of the workflow) |

## Running the examples

```bash
cd examples/math
sp conduct . --auto-accept
uv run python -m pytest tests/ -v
```

The conductor resolves dependencies automatically: `factorial` and `is_prime` compile
first, then `math_demo` (which depends on both), then `math_workflow`.

## What each spec demonstrates

### `bundle` — math_utils

`math_utils.spec.md` shows the compact bundle format: a YAML function block where each
entry has `inputs`, `outputs`, and a one-line `behavior`. No full sections — just a
compact description of related functions. Use this format when functions are simple
enough to describe in a sentence each.

### `function` — factorial, is_prime

`factorial.spec.md` and `is_prime.spec.md` show the full function format: numbered
sections for Behavior, Constraints, Contract, and a Test Scenarios table. Use `function`
when a single operation has enough edge cases, constraints, and contract conditions to
warrant its own dedicated spec.

### `type` — user

`user.spec.md` shows how to specify a data structure. The yaml:schema block defines
field names, types, formats, and required fields. The `# Constraints` section adds
cross-field rules that can't be expressed in schema alone, and the `# Examples` table
gives concrete valid and invalid instances.

### `module` — math_demo

`math_demo.spec.md` shows how to aggregate sub-specs. A module spec lists what it
re-exports and documents the top-level entry points — it doesn't re-specify behaviour
that `factorial` and `is_prime` already cover.

### `workflow` — math_workflow

`math_workflow.spec.md` shows the yaml:steps format. Each step references a spec by
name, wires inputs from either the workflow's own inputs (`inputs.n`) or a previous
step's outputs (`compute_factorial.outputs.result`). The `checkpoint: true` flag on
`check_prime` means the workflow can resume from that step if the first step succeeds
but the second fails.
