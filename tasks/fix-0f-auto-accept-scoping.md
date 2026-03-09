# Task: Fix `--auto-accept` Permission Scoping (IMPROVEMENTS.md §0f)

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.
The CLI lives in `src/specsoloist/cli.py`.

## Problem

`_run_agent_oneshot()` in `cli.py` passes `--permission-mode bypassPermissions` to Claude
whenever `--auto-accept` is set. This is intentional for quine runs (`sp conduct score/`)
where fully autonomous operation is the goal — but the same flag is applied to every
agent command: `sp fix`, `sp compose`, `sp respec`, `sp conduct` on a normal project.

There has already been one incident where a soloist ignored its output path and wrote to
`src/` instead of `build/quine/` — it was caught only because someone noticed the git diff.
With `bypassPermissions` that write went through silently.

## What to Fix

In `src/specsoloist/cli.py`, in `_run_agent_oneshot()`:

```python
def _run_agent_oneshot(agent: str, prompt: str, auto_accept: bool, model: str | None = None,
                       is_quine: bool = False):
```

The `is_quine` parameter already exists. Use it:

- **When `is_quine=True`**: keep the current behaviour — pass `--permission-mode bypassPermissions`.
  Quine runs are intentionally fully autonomous and write to a sandboxed `build/quine/` directory.
- **When `is_quine=False` and `auto_accept=True`**: do NOT pass `bypassPermissions`.
  Instead pass `--dangerously-skip-permissions`. This skips interactive approval prompts
  (what the user asked for) without granting unrestricted filesystem access.
- **When `auto_accept=False`**: pass nothing (let Claude's default permission mode apply,
  which prompts the user for each tool use). This is already the case for gemini.

Check whether `--dangerously-skip-permissions` is the correct flag for Claude CLI (it was the
older flag; newer versions use `--permission-mode`). Run `claude --help` to confirm the
available options, and use whichever is appropriate for the installed version.

## Files to Read First

- `src/specsoloist/cli.py` — the full file, especially `_run_agent_oneshot()` and all callers
- `AGENTS.md` — project context

## Success Criteria

1. `_run_agent_oneshot()` only passes `bypassPermissions` when `is_quine=True`.
2. `--auto-accept` without `is_quine` uses the least-privileged flag that still skips prompts.
3. All existing tests still pass: `uv run python -m pytest tests/`
4. Ruff passes: `uv run ruff check src/`
5. The change is covered by a test in `tests/test_cli_doctor_status.py` or a new
   `tests/test_cli_permissions.py` that confirms the correct flags are constructed for
   each combination of `(auto_accept, is_quine)`.
