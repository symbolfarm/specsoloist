# HK-19: Fix `score/cli.spec.md` — quine correctness

**Effort**: Small (< 30 min)

## Problem

`score/cli.spec.md` has three gaps that would cause the quine to generate incorrect code:

1. `sp perform` is still documented (removed in HK-03). Running the quine would regenerate a CLI that implements a deleted command.
2. `--version`/`-V` global flag is missing from the Global Flags section.
3. `--arrangement` flag is missing from the `sp list`, `sp status`, and `sp graph` entries.

These gaps also mean `sp validate score/cli.spec.md` passes when it shouldn't.

## Steps

Read `score/cli.spec.md` in full first to understand its structure, then:

1. **Remove `sp perform`** — find the line that documents it (around the Workflow section) and delete it along with any surrounding context that only exists because of it.

2. **Add `--version`/`-V` to Global Flags** — the spec already has a Global Flags section; add:
   - `--version` / `-V`: print `specsoloist X.Y.Z` and exit 0

3. **Add `--arrangement` to `sp list`, `sp status`, `sp graph`** — each of these commands gained `--arrangement <file>` in HK-15. Add the flag to each command's entry with a brief description: "Load arrangement file to apply `specs_path` for spec discovery."

## Verification

- `sp validate cli` passes with 0 errors (run from repo root with `ANTHROPIC_API_KEY` set)
- Scan the updated spec: no reference to `sp perform`
- `--version` and `--arrangement` both appear in the spec

## Files to Read

- `score/cli.spec.md` — the spec being fixed
- `src/specsoloist/cli.py` lines 35–45 — argparse entries for `--version`/`-V`
- `src/specsoloist/cli.py` — search for `arrangement_arg` to see `--arrangement` usage
