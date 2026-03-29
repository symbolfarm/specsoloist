# Task 37: Make `sp diff --all` the default behavior + daily CI drift check

**Effort:** Small–Medium
**Depends:** —

## Context

`sp diff <name>` compares a single spec against its implementation, reporting drift.
`sp diff --all` iterates over every spec and reports drift for all of them.

Users almost always want the `--all` behavior — running `sp diff` with no arguments
should show drift for the entire project. The single-spec mode should still be available
via `sp diff <name>`.

Additionally, spec drift should be caught automatically. `sp diff` is cheap (AST-based,
no LLM calls), so it can run daily in CI to flag specs that have fallen behind the code.
This catches the exact problem seen in the 2026-03-30 quine CI failure: task 35 added
leaf-name resolution to the resolver code but not the spec.

## Steps

1. **Read** `src/specsoloist/cli.py` — find the `diff` subparser and `cmd_spec_diff` dispatch
2. **Change default**: When `sp diff` is invoked with no positional arg, run the all-specs
   path (currently behind `--all`). Keep `sp diff <name>` for single-spec mode.
3. **Remove or repurpose `--all`**: If the flag becomes redundant, remove it. Alternatively,
   keep it as a no-op with a deprecation note.
4. **Add daily CI workflow**: `.github/workflows/spec-drift.yaml` — runs `sp diff` (all specs)
   against `score/arrangement.yaml`. Fails if any spec has MISSING or TEST_GAP issues.
   Schedule: daily (cheap, no LLM calls). Could also be a step in the existing quine workflow,
   but a separate workflow means it runs even when the quine is skipped.
5. **Update docs**: `docs/reference/cli.md`, README CLI table if needed
6. **Tests**: Update existing diff tests to match new default; add a test that `sp diff`
   with no args runs all specs

## Files to Read

- `src/specsoloist/cli.py` (diff subparser + cmd_spec_diff + cmd_diff)
- `tests/test_spec_diff.py`
- `.github/workflows/quine.yaml` (for CI pattern reference)
- `docs/reference/cli.md`

## Success Criteria

- `sp diff` (no args) shows drift for all specs in the project
- `sp diff <name>` still works for a single spec
- Daily CI workflow runs `sp diff` and fails on drift
- Existing tests updated and passing
