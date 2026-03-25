# HK-15: `specs_path` Arrangement Field + Arrangement-Aware Discovery Commands

## Problem

`sp list`, `sp status`, and `sp graph` always look for specs in `src/`, which is
SpecSoloist's default but not universal. Projects like definitree store specs in
`specs/`. There is currently no way to configure this via `arrangement.yaml`, and
these commands do not load the arrangement at all.

Running any of these in a project whose specs aren't in `src/` produces:

```
! Warning: No specs found in src/
```

`sp conduct` already accepts a positional `src_dir` argument and loads the arrangement
for output paths — the discovery commands need the same treatment.

## What to Change

### 1. `schema.py` — add `specs_path` to `Arrangement`

```python
specs_path: str = Field(
    default="src/",
    description="Directory where spec files (.spec.md) are stored. "
                "Used by sp list, sp status, sp graph, and sp conduct."
)
```

Place it after `target_language` and before `output_paths` so it reads logically.

### 2. `cli.py` — add `--arrangement` flag to `list`, `status`, `graph`

Each of these three subparsers currently has no flags. Add:

```python
list_parser.add_argument("--arrangement", metavar="FILE",
                         help="Path to arrangement YAML (auto-discovers arrangement.yaml)")
status_parser.add_argument("--arrangement", metavar="FILE",
                           help="Path to arrangement YAML (auto-discovers arrangement.yaml)")
# graph already has no parser variable — promote it from add_parser to a variable first
graph_parser = subparsers.add_parser("graph", help="Export dependency graph as Mermaid")
graph_parser.add_argument("--arrangement", metavar="FILE",
                          help="Path to arrangement YAML (auto-discovers arrangement.yaml)")
```

### 3. `cli.py` — apply `specs_path` from arrangement in `cmd_list`, `cmd_status`, `cmd_graph`

These three commands call `core.list_specs()` which uses `core.parser.src_dir`. After
loading the arrangement, update the parser:

```python
def cmd_list(core: SpecSoloistCore, arrangement_arg: str | None = None):
    arrangement = _resolve_arrangement(core, arrangement_arg)
    if arrangement:
        core.parser.src_dir = os.path.abspath(arrangement.specs_path)
    specs = core.list_specs()
    if not specs:
        path = arrangement.specs_path if arrangement else "src/"
        ui.print_warning(f"No specs found in {path}")
        ...
```

Apply the same pattern to `cmd_status` and `cmd_graph`.

`_resolve_arrangement` is already implemented and auto-discovers `arrangement.yaml` in
the cwd when no explicit path is given. No new discovery logic is needed.

### 4. `cli.py` — update call sites in `main()`

Pass `getattr(args, "arrangement", None)` to `cmd_list`, `cmd_status`, `cmd_graph`.

### 5. `score/arrangement.spec.md` — document the new field

Add `specs_path` to the field list with its default and purpose.

## Files to Read

- `src/specsoloist/schema.py` — `Arrangement` model, field placement conventions
- `src/specsoloist/cli.py` — `_resolve_arrangement`, `_apply_arrangement`, `cmd_list`,
  `cmd_status`, `cmd_graph`, the `main()` dispatch block
- `score/arrangement.spec.md` — to see the existing field documentation pattern

## Success Criteria

- `sp list` in a project with `specs_path: specs/` in `arrangement.yaml` discovers
  all specs in `specs/` without any `--arrangement` flag
- `sp list --arrangement path/to/other.yaml` uses that file's `specs_path`
- The "No specs found" warning message includes the actual configured path
- `sp conduct specs/` continues to work unchanged (it sets `src_dir` directly)
- All 355 tests pass; `uv run ruff check src/` clean

## Tests

Add to `tests/test_schema.py` (or a new `tests/test_arrangement.py`):
- `Arrangement` loads with `specs_path` defaulting to `"src/"`
- `Arrangement` with explicit `specs_path: "specs/"` serialises and deserialises correctly

Add to `tests/test_cli.py` (or the existing CLI test file):
- `cmd_list` with a mock arrangement that has `specs_path: "specs/"` updates
  `core.parser.src_dir` before calling `list_specs()`
