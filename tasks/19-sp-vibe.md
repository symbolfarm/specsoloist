# Task 19: `sp vibe` — Single-Command Autonomous Pipeline

## Why

The primary use-case for SpecSoloist is: give a high-level brief, get a working application.
The pipeline already exists in pieces (`sp compose` → `sp conduct`). This task stitches
them into a single command with good UX and configurable review pauses.

## Design Decisions (resolved)

- **Default: hands-off.** No pauses. `sp vibe` runs compose then conduct autonomously.
- **Prompt file preferred.** If passed a `.md` file, read it as the brief. A plain string
  is accepted for quick use but the file format is the primary interface.
- **Existing project support.** `sp vibe` should work in a directory that already has
  specs and/or code — it should compose only what's missing and conduct only what needs
  building. This is a "run on existing project" capability.
- **First pass: keep it simple.** Ship the basic pipeline. Review pauses, dashboard
  integration, and interactive modes are follow-on work.

## Interface

```bash
# Hands-off (default): compose → conduct → test
sp vibe brief.md
sp vibe brief.md --template python-fasthtml

# Pause after specs are written (user reviews, edits, then presses Enter)
sp vibe brief.md --pause-for-review

# Run on an existing project — compose addendum specs, conduct only new/stale ones
sp vibe brief.md --resume

# Quick string brief (for simple requests)
sp vibe "Add a delete button to the todo app"
```

## Brief File Format

A Markdown file accepted by `sp compose`. No special schema required for the first pass —
`sp compose` already handles free-form natural language. A richer structured format
(with stack, must-have, nice-to-have sections) can be added later.

## Existing Project Behaviour

When run in a directory that already has `specs/` and compiled code:
- `sp compose` receives the brief + a listing of existing specs as context
  (this is already how `sp compose` works — it incorporates existing specs)
- `sp conduct --resume` is used so already-compiled specs are skipped
- The net effect: the brief is treated as an addendum or feature request, not a
  full rewrite

## Files to Read

- `src/specsoloist/cli.py` — `cmd_compose()` and `cmd_conduct()`; add `cmd_vibe()` here
- `src/specsoloist/arrangements/` — template names for `--template` passthrough

## Implementation

1. Add `vibe` subparser to `main()` with args: `brief` (positional, optional), `--template`,
   `--pause-for-review`, `--resume`, `--no-agent`, `--auto-accept`, `--model`
2. `cmd_vibe()`:
   - If `brief` ends in `.md`, read the file contents as the compose request
   - Otherwise use `brief` as a string directly
   - Call `cmd_compose(core, request, ...)` — this writes specs to `specs/`
   - If `--pause-for-review`: print spec list and `input("Edit specs if needed, then press Enter to build: ")`
   - Call `cmd_conduct(core, ..., resume=args.resume)` — builds everything
3. Update `README.md` Quick Start to use `sp vibe` as the primary workflow example

## Success Criteria

- `sp vibe brief.md` runs end-to-end: compose then conduct, no pause
- `sp vibe "Add delete button"` works with a plain string
- `--pause-for-review` pauses between compose and conduct
- `--resume` passes through to conduct (skips already-compiled specs)
- Works in an empty directory and in a directory with existing specs
- `sp vibe --help` documents all options
- All 270 tests still pass, ruff clean

## Tests

- `sp vibe` with a file brief calls compose then conduct in sequence
- `sp vibe` with a string brief works the same way
- `--pause-for-review` inserts a pause (mock `input()`)
- `--resume` flag passes through to conduct
