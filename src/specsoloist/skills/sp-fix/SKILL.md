---
name: sp-fix
description: Fix failing tests for a SpecSoloist spec by analyzing errors and patching the implementation. Use when tests are failing after compilation, when asked to fix a broken spec or auto-heal test failures, or when `sp compile` or `sp conduct` produced code that does not pass its tests.
license: MIT
compatibility: Requires specsoloist CLI (`pip install specsoloist` or `uv add specsoloist`). Designed for Claude Code and compatible agents.
metadata:
  author: symbolfarm
  version: "0.3.2"
---

# sp-fix: Fix Failing Tests

## When to use this skill

- Tests are failing after `sp compile` or `sp conduct`
- User asks to fix a specific spec
- Auto-healing is needed after a bad compilation
- User says "the tests are broken for X"

## How to fix

### With the CLI (recommended)

```bash
sp fix <spec-name>
```

**Examples:**
```bash
sp fix resolver                         # Fix failing tests for the resolver spec
sp fix auth --model claude-opus-4-6    # Use a specific model
```

### What it does

1. Runs the current test suite for the spec
2. Analyzes failure output
3. Identifies the root cause (implementation bug, test bug, or spec ambiguity)
4. Patches the implementation or tests
5. Re-runs tests — retries up to 3 times

## The key principle

**The spec is the source of truth.** If tests and code disagree with the spec, fix the code/tests — not the spec.

If the spec itself is ambiguous or incorrect, that is a separate problem: edit the spec first, then recompile.

## When not to use this skill

- If the spec is wrong or ambiguous → edit the spec, then recompile with `sp compile`
- If tests are testing the wrong behavior → review the spec first
- If there are import/dependency errors → check that dependencies are compiled with `sp conduct`

## Tips

- Run `sp test <name>` first to see the full failure output
- Check that all dependency specs are compiled and up-to-date
- For complex failures, read the spec and implementation together to find the mismatch
