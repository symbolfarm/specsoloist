# Task 28: Wire event emission into core, runner, and compiler

**Effort**: Medium

**Depends on**: Task 27 (event bus)

## Motivation

Task 27 creates the event bus infrastructure but doesn't emit any events. This task adds
`_emit()` calls at the natural boundaries in the compilation pipeline so that subscribers
can observe a build in real time.

## Design Decisions (locked)

- **Emission points are at method boundaries**, not inside methods. We emit "started" at the
  top and "completed"/"failed" at the bottom. No mid-method events (those are for future
  granularity).
- **Duration tracking**: "completed" events include `duration_seconds` in their data dict,
  measured with `time.monotonic()` around the operation.
- **Error capture**: "failed" events include `error` (str) and `error_type` (str) in data.
- **No changes to return types or method signatures** beyond what task 27 already added.
  This task only adds `self._emit(...)` calls inside existing methods.

## Emission Points

### `src/specsoloist/core.py`

| Location | Event Type | Data |
|----------|-----------|------|
| `compile_project()` top | `build.started` | `total_specs`, `build_order`, `parallel` |
| `compile_project()` end | `build.completed` | `specs_compiled`, `specs_failed`, `duration_seconds` |
| `_compile_project_parallel()` per level | `build.level.started` | `level`, `spec_names` |
| `_compile_single_spec()` top | `spec.compile.started` | `dependencies` |
| `_compile_single_spec()` success | `spec.compile.completed` | `output_path`, `duration_seconds` |
| `_compile_single_spec()` failure | `spec.compile.failed` | `error`, `error_type` |
| `attempt_fix()` top | `spec.fix.started` | `attempt` |
| `attempt_fix()` end | `spec.fix.completed` | `success`, `duration_seconds` |

### `src/specsoloist/runner.py`

| Location | Event Type | Data |
|----------|-----------|------|
| `run_tests()` top | `spec.tests.started` | — |
| `run_tests()` end | `spec.tests.completed` | `success`, `duration_seconds`, `return_code` |

Runner needs access to the event bus. Pass it through from core (runner is already created
in core's `__init__`).

### `src/specsoloist/compiler.py`

No direct emission here — the compiler is a pure function (prompt in, code out). LLM-level
events are handled in task 29 (provider token tracking).

## Tests

- `tests/test_event_emission.py`
- Mock event bus, run `compile_project()` with a trivial spec, assert expected event sequence
- Verify `build.started` comes first, `build.completed` comes last
- Verify `spec.compile.started` and `spec.compile.completed` bracket each spec
- Verify failed specs emit `spec.compile.failed`
- Verify duration_seconds is a positive float

## Files to Read Before Starting

- `src/specsoloist/core.py` — all of it; understand every method that will get emission points
- `src/specsoloist/runner.py` — `run_tests()` and `__init__`
- `src/specsoloist/events.py` — the event bus from task 27
- `tests/test_core.py` — existing test patterns to follow

## Success Criteria

- `uv run python -m pytest tests/test_event_emission.py` passes
- `uv run python -m pytest tests/` — all existing tests still pass
- `uv run ruff check src/` — clean
- A `compile_project()` call with a mock bus produces the full expected event sequence
