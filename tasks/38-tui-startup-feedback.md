# Task 38: TUI startup feedback

**Effort:** Small
**Depends:** 31d

## Context

When running `sp conduct --no-agent --tui`, the TUI shows "No build in progress" until
the build thread emits its first `build.started` event. This can take several seconds
(spec parsing, dependency resolution, first API call), leaving the user with no indication
that anything is happening. Users may quit thinking it's broken.

## Steps

1. **Read** `src/specsoloist/tui.py` — understand the StatusBar and initial state
2. **Add a "build pending" state**: When `DashboardApp` is created with the intent to run
   a build (vs connecting to an SSE stream), it should show "Initializing build..." or
   similar instead of "No build in progress"
3. **Option A** — `DashboardApp.__init__` accepts a `build_pending: bool = False` parameter.
   When true, StatusBar renders "Initializing build..." until the first `refresh_state()` call.
4. **Option B** — `_run_with_tui()` in `cli.py` calls `app.refresh_state()` with a synthetic
   "idle but starting" state before launching the build thread.
5. **Update tests**: Add a test that confirms the pending message appears before any events.

## Files to Read

- `src/specsoloist/tui.py`
- `src/specsoloist/cli.py` (`_run_with_tui`)
- `tests/test_tui.py`

## Success Criteria

- TUI shows an immediate "Initializing build..." (or similar) message on launch
- Message transitions to normal build display once the first event arrives
- No regression in headless tests
