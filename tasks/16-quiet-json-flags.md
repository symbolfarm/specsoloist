# Task 16: `--quiet` / `--json` Output Flags

## Why

SpecSoloist currently always emits Rich terminal output (spinners, coloured panels, tables).
This makes it unusable in:
- CI pipelines (spinners render as garbage)
- Makefiles and shell scripts (output parsing is fragile)
- Editor integrations (need machine-readable state)

## Files to Read

- `src/specsoloist/cli.py` — main CLI; all `ui.*` calls go through here
- `src/specsoloist/ui.py` (or wherever the Rich console is initialised)

## Behaviour

### `--quiet`
Suppress all non-error output. Only print errors and final pass/fail status.
Useful for CI and scripting.

```bash
sp compile parser --quiet   # prints nothing on success; prints error on failure
sp conduct --quiet          # only prints final "X specs compiled, Y failed"
```

Rich has `Console(quiet=True)` — this may be implementable by passing a flag through
to the console initialisation rather than adding conditionals everywhere.

### `--json`
Emit structured JSON to stdout instead of Rich output. Each command produces a
single JSON object (or newline-delimited objects for multi-spec commands).

```bash
sp status --json
# {"specs": [{"name": "parser", "compiled": true, "tests_pass": true, "last_built": "..."}]}

sp compile parser --json
# {"spec": "parser", "success": true, "tests_pass": true, "errors": []}
```

Commands to support initially: `sp status`, `sp compile`, `sp validate`, `sp diff`.

## Implementation Notes

- Add `--quiet` and `--json` as global flags in the top-level `main()` argparse setup
  (before subparsers), so they work on all commands.
- Store the flags in a module-level or passed context so `ui.py` functions can check them.
- For `--json`: the data is already in Pydantic models or dicts — serialisation is trivial.
  Disable the Rich console entirely and use `print(json.dumps(...))`.
- `NO_COLOR` env var is already respected — `--quiet` and `--json` should also disable
  Rich output even if `NO_COLOR` is not set.

## Success Criteria

- `sp status --json` produces valid JSON parseable by `jq`
- `sp compile parser --quiet` produces no output on success
- `sp compile parser --quiet` prints an error message (not a Rich panel) on failure
- `--quiet` and `--json` appear in `sp --help`
- All 270 tests still pass, ruff clean

## Tests

Add to an appropriate test file:
- `--json` flag produces valid JSON for `sp status`
- `--quiet` flag suppresses normal output
- Errors still appear under `--quiet`
