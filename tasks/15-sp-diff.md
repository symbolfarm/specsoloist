# Task 15: `sp diff` — Spec vs Code Drift Detection

## Why

There is currently no way to ask "does this module's implementation match its spec?"
This gap becomes critical when:
- Code is modified after a spec was written (drift)
- A quine run produces output that differs from the original source
- You want to verify a soloist implemented everything the spec required

A generalised `sp diff` command solves all three cases.

## Scope

This task implements a working `sp diff <name>` for a single spec vs its compiled
implementation. Run-over-run diff (archives) is a follow-on task.

## Existing Work

`score/build_diff.spec.md` already exists. Read it — it may be compilable as-is via
`sp compile build_diff`. If so, use that as the implementation starting point.

## Files to Read

- `score/build_diff.spec.md` — existing spec for the diff tool
- `src/specsoloist/cli.py` — where `cmd_diff` likely already has a stub
- `src/specsoloist/core.py` — for understanding how specs and compiled files are located
- `src/specsoloist/manifest.py` — to find where compiled output paths are stored

## Behaviour

```bash
sp diff parser           # compare score/parser.spec.md vs src/specsoloist/parser.py
sp diff parser --json    # machine-readable output
```

For each spec, report:

1. **Missing symbols** — functions/types named in spec but not found in compiled code
2. **Undocumented symbols** — exported functions in code not mentioned in spec
3. **Test gaps** — behaviours described in spec `## Test Scenarios` with no corresponding
   test function name in the test file

Output format (terminal):
```
parser — 3 issues
  ✗ MISSING   parse_workflow_spec  (in spec, not in src/specsoloist/parser.py)
  ⚠ UNDOCUMENTED  _parse_frontmatter  (in code, not in spec)
  ⚠ TEST GAP  "Returns empty list when no functions defined"  (scenario, no test found)
```

Exit code: 0 if no issues, 1 if any MISSING or TEST GAP found.

## Implementation Notes

- Symbol extraction from Python: use `ast` module to parse the compiled `.py` file
  and extract top-level function/class names. Do not use `importlib` (avoids execution).
- Symbol extraction from spec: parse the spec's `## Functions` or `yaml:functions` block
  for declared names. Bundle specs have `yaml:functions`; function specs have a single name.
- Test gap detection: parse the test file for function names starting with `test_`;
  fuzzy-match against scenario descriptions from the spec's `## Test Scenarios` section.
  Exact matching is hard — flag as a gap only when no test name contains any word from
  the scenario description.
- Start simple: missing symbols is the highest-value check. Ship that first.

## Success Criteria

- `sp diff <name>` runs without error on any compiled spec
- Correctly identifies at least one real discrepancy when tested on a spec known to have drift
- `sp diff --help` documents usage
- `uv run python -m pytest tests/ -q` still passes
- `uv run ruff check src/` clean

## Tests

Add `tests/test_diff.py` covering:
- Spec and code in sync → 0 issues
- Function in spec but not in code → reported as MISSING
- Function in code but not in spec → reported as UNDOCUMENTED
- `--json` flag produces parseable output
