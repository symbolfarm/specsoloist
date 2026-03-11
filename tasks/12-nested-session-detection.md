# Task: Detect and Warn on Nested Claude Code Session

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.

`sp conduct` works by spawning a conductor agent as a subprocess (`claude --print ...`).
When Claude Code is already running (i.e. the user is in an active Claude Code session),
this subprocess invocation fails silently or with a confusing error — Claude detects the
nesting and refuses to start a second session.

This is a real friction point: a developer using Claude Code to help build their project
might naturally try `sp conduct` from a Claude Code terminal, hit a confusing error, and
not understand why.

The fix is two-part: detect the condition early and give a clear, actionable message.

## What to Build

### 1. Detection

Claude Code sets environment variables that can be detected at runtime. Check for:
- `CLAUDE_CODE_SESSION` — set by Claude Code in its terminal environment
- `ANTHROPIC_CLAUDE_CODE` — alternate indicator
- `TERM_PROGRAM=claude` or similar

Research which environment variable is reliably set by the current version of Claude Code.
Run `env | grep -i claude` inside a Claude Code terminal to identify the right variable.

If none is reliably set, fall back to checking whether the parent process name contains
`claude` via `psutil` or `/proc/{ppid}/comm` on Linux.

### 2. Warning in `sp conduct` (and `sp compose`, `sp fix`, `sp respec`)

In `_run_agent_oneshot()` in `src/specsoloist/cli.py`, before invoking the Claude subprocess:

```
╭─────────────────────── Heads Up ────────────────────────────╮
│ You appear to be running inside Claude Code.                 │
│                                                              │
│ sp conduct spawns a Claude subprocess, which may be blocked  │
│ inside an active Claude Code session.                        │
│                                                              │
│ Options:                                                      │
│  1. Open a separate terminal outside Claude Code             │
│  2. Use --no-agent to compile without an agent               │
│  3. If you are Claude Code: use the Agent tool to spawn      │
│     the conductor agent directly (no subprocess needed)      │
╰──────────────────────────────────────────────────────────────╯
```

This should be a warning, not an error. Some setups may work; others won't. Let the user
decide whether to proceed. If `--auto-accept` is set, print the warning but continue.

### 3. Graceful failure message

If the subprocess invocation does fail (non-zero exit with no useful output, or a specific
error pattern), catch it and print:

```
✖ The conductor agent failed to start.
  This often happens when running sp conduct inside Claude Code.
  Try running from a separate terminal, or use --no-agent.
```

Currently this failure likely surfaces as a generic Python error or empty output.

### 4. Documentation

Update the following with a note about nested sessions:
- `README.md` — "Running sp conduct" section
- `docs/` — conductor/agent guide
- The relevant `--help` text for `sp conduct`

### 5. Gemini CLI equivalent (if applicable)

Check whether the Gemini CLI has a similar constraint when run inside a Gemini CLI session.
If it does, apply the same detection and warning for `gemini` subprocess calls.

## Files to Read First

- `src/specsoloist/cli.py` — `_run_agent_oneshot()`, `cmd_conduct()`
- `README.md` — existing conductor documentation
- `AGENTS.md`

## Success Criteria

1. Running `sp conduct` inside a Claude Code terminal prints the warning.
2. Running `sp conduct` outside Claude Code shows no warning.
3. The warning is shown for `sp conduct`, `sp compose`, `sp fix`, `sp respec` — all
   commands that spawn a Claude subprocess.
4. If the subprocess fails with a nesting-related error, the error message is friendly
   and actionable.
5. `--no-agent` bypasses the warning (since `--no-agent` doesn't spawn a subprocess).
5a. The warning message mentions all three options (separate terminal, `--no-agent`, Agent tool for Claude Code sessions).
6. All existing tests pass: `uv run python -m pytest tests/`
7. Ruff passes: `uv run ruff check src/`

## Notes

If `psutil` is needed for process name detection, add it as an optional dependency with a
graceful fallback: `try: import psutil; ...` — if unavailable, skip the parent process check.
Don't add `psutil` as a hard dependency.
