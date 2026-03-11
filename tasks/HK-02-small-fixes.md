# HK-02: Small Fixes (type hint, comment, arrangement warning propagation)

Three small, mechanical fixes surfaced during task 05 work. No design decisions required.

## Fixes

### 1. `Optional[ArrangementEnvironment]` type hint lie (`schema.py`)

`Arrangement.environment` is declared as `Optional[ArrangementEnvironment]` but has
`default_factory=ArrangementEnvironment`, so it is never actually `None`. The `Optional`
type hint is misleading — it causes unnecessary `if arrangement.environment and ...`
guards downstream (e.g. in `compiler.py` after the task 05 change).

Fix: change the field to `ArrangementEnvironment = Field(default_factory=ArrangementEnvironment)`.
Update any downstream guards that check for `None` on `arrangement.environment`.

### 2. Missing comment on reference spec early return (`core.py`)

`_compile_single_spec()` now returns early for reference specs (§0g fix from HK-01)
but the intent isn't obvious to a reader — it looks like a silent no-op next to the
manifest update logic. Add a one-line comment explaining why.

```python
# Reference specs produce no output files; manifest tracking and test
# generation are not applicable.
if spec.metadata.type == "reference":
    return {"success": True, "error": ""}
```

### 3. Arrangement dependency warning only fires from `sp validate` (`cli.py`)

`_check_arrangement_dependencies()` warns when `dependencies` is set but no install
command is in `setup_commands`. Currently this check is only triggered by
`sp validate --arrangement`. But the warning is most useful at arrangement load time —
any command that loads an arrangement (`sp compile`, `sp build`, `sp conduct`) could
benefit from it.

Fix: move the check into `_resolve_arrangement()` so it fires whenever an arrangement
is loaded. `_resolve_arrangement()` already prints info about the loaded arrangement,
so a warning fits naturally there. Remove the explicit call from `cmd_validate`.

## Files to Change

- `src/specsoloist/schema.py` — fix `Optional[ArrangementEnvironment]`
- `src/specsoloist/core.py` — add comment
- `src/specsoloist/cli.py` — move warning to `_resolve_arrangement()`, clean up `cmd_validate`

## Success Criteria

1. `Arrangement.environment` is typed as `ArrangementEnvironment` (non-optional).
2. Downstream `if arrangement.environment` guards removed or updated accordingly.
3. Comment present on the reference spec early return in `_compile_single_spec`.
4. `_check_arrangement_dependencies` called from `_resolve_arrangement`, not `cmd_validate`.
5. All existing tests pass: `uv run python -m pytest tests/`
6. Ruff passes: `uv run ruff check src/`
