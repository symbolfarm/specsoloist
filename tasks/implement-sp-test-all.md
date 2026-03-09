# Task: Implement `sp test --all`

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.
The CLI lives in `src/specsoloist/cli.py`. The existing `sp test <name>` command runs tests
for a single spec. `sp status` shows the manifest state but does not re-run tests.

## What to Build

Add a `--all` flag to the existing `sp test` command so that:

```
sp test --all
```

Runs tests for every spec that has a compiled implementation on disk, shows a results table,
and exits 1 if any test suite failed.

### Parser change

In `main()`, change the `test` subparser from requiring a positional `name` argument to
making it optional, with `--all` as the alternative:

```python
test_parser.add_argument("name", nargs="?", help="Spec name to test (omit with --all)")
test_parser.add_argument("--all", action="store_true", dest="test_all",
                         help="Run tests for every compiled spec")
```

If neither `name` nor `--all` is provided, print an error and exit 1.

### `cmd_test` change

Extend `cmd_test` to handle the `--all` case:

```
Running all tests...

  Spec         Result    Duration
  ──────────────────────────────
  config       PASS      0.4s
  resolver     PASS      0.8s
  parser       FAIL      1.2s
  manifest     PASS      0.3s

  3 passed, 1 failed
```

- Use `core.list_specs()` to find all specs.
- For each spec, check whether the implementation file exists on disk before running
  (skip and show `NO BUILD` if not yet compiled — don't error).
- Run `core.run_tests(name)` for each; collect results.
- Display the summary table using `ui.create_table`.
- Print `ui.print_success` or `ui.print_error` with the totals.
- Exit 1 if any spec failed.

Duration is the wall-clock time for each `run_tests()` call; use `time.perf_counter()`.

### Determining whether a spec is compiled

The build manifest (`core._get_manifest()`) records `output_files` for each compiled spec.
Check whether at least one non-test output file exists on disk. If the manifest has no entry
for a spec, treat it as not compiled and skip it with a `DIM` `NO BUILD` in the Result column.

## Files to Read First

- `src/specsoloist/cli.py` — especially `cmd_test`, `cmd_status`, `main()`
- `src/specsoloist/core.py` — `run_tests()`, `list_specs()`
- `src/specsoloist/manifest.py` — `BuildManifest`, `SpecBuildInfo`
- `src/specsoloist/ui.py` — `create_table`, `print_success`, `print_error`

## Success Criteria

1. `sp test myspec` still works exactly as before (no regression).
2. `sp test --all` runs all compiled specs and shows the table.
3. `sp test` (no args) prints a usage error and exits 1.
4. Exits 0 if all pass, 1 if any fail or no specs were compiled.
5. All existing tests pass: `uv run python -m pytest tests/`
6. Ruff passes: `uv run ruff check src/`
7. New tests added to `tests/test_cli_test_all.py` covering:
   - `sp test --all` with no compiled specs (exits 0, shows 0 specs)
   - `sp test --all` with a manifest that has no matching files on disk (all show NO BUILD)
   - The argument parser rejects `sp test` with no args
