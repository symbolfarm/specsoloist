# Task 19: `sp vibe` — Single-Command Autonomous Pipeline

## Status: DISCUSS WITH USER BEFORE STARTING

Key design decisions need to be made before implementation. Read this task and
output `NEEDS_HUMAN` if picked up by the ralph loop.

## Why

The primary use-case for SpecSoloist is: give a high-level brief, get a working application.
The pipeline already exists in pieces (`sp compose` → `sp conduct`). This task stitches
them into a single command with good UX and configurable review pauses.

## Proposed Interface

```bash
sp vibe "A Tamagotchi-style pet game with a local LLM personality"
sp vibe brief.md --template python-fasthtml
sp vibe brief.md --template python-fasthtml --pause-for-review
sp vibe brief.md --auto   # no pauses, fully autonomous
```

## Pause Modes (to decide)

- `--pause-for-review` — stop after specs are written; user edits specs manually,
  presses enter to continue with `sp conduct`
- `--interactive` — pause after each spec for incremental approval (may be too slow)
- `--auto` — no pauses (compose then conduct immediately)
- Default behaviour TBD — pause-for-review seems safest for a first release

## Brief File Format (to decide)

Should `sp vibe` accept:
a) A plain string prompt (like `sp compose` currently does)
b) A structured Markdown brief file (richer input, see IDEAS.md §1b)
c) Both

## Open Questions for User

1. Should `--pause-for-review` be the default, or should `--auto` be default?
2. Should the brief file format be defined now, or keep it as a plain string first?
3. Is `sp vibe` the right name? Alternatives: `sp run`, `sp build-app`, `sp go`
4. Should this integrate with the structured build events (task for dashboard) from the start,
   or keep it simple and add observability later?

## Implementation (once decisions made)

- New `cmd_vibe()` in `cli.py` that calls `cmd_compose()` then optionally pauses then
  calls `cmd_conduct()`
- The pause is a simple `input("Specs written to specs/. Edit them, then press Enter to build: ")`
- Brief file: if argument ends in `.md`, read it as the compose request; otherwise treat
  as a plain string
- `--template` passes through to arrangement selection (already implemented in `sp init`)

## Success Criteria

- `sp vibe "brief"` runs compose then conduct end-to-end
- `--pause-for-review` pauses between compose and conduct
- `sp vibe --help` documents all options
- End-to-end smoke test passes
