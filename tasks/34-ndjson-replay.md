# Task 34: `sp dashboard --replay` and `--follow` for NDJSON log files

**Effort**: Small

**Depends on**: Task 31b (Textual app skeleton)

## Motivation

A replay mode that feeds an NDJSON log file into the TUI at accelerated speed lets people
experience the dashboard without running an actual LLM build. Useful for:

- README demos and animated GIFs
- Conference talks / presentations
- Testing the TUI during development without burning API credits
- Sharing build logs with collaborators ("here's what happened")

A follow mode (`--follow`) tails a growing NDJSON log file in real time, like `tail -f`.
This bridges agent mode to the TUI: run `sp conduct --log-file build.ndjson` in one
terminal and `sp dashboard --follow build.ndjson` in another. The agent writes events
as NDJSON; the dashboard tails them live.

## Design

```bash
sp dashboard --replay build.ndjson              # replay at 10x speed
sp dashboard --replay build.ndjson --speed 1    # real-time replay
sp dashboard --replay build.ndjson --speed 0    # instant (no delays)
sp dashboard --follow build.ndjson              # tail a live log file
```

### How replay works

1. Read NDJSON file line by line
2. Parse each line as a `BuildEvent` (reconstruct from JSON)
3. Calculate delay between consecutive events from timestamps
4. Feed events into the TUI's `BuildState` at `speed` multiplier
5. When file is exhausted, show final state and wait for `q` to quit

### How follow works

1. Read existing file content (catch up to current state)
2. Feed all existing events into BuildState
3. Then tail for new lines, polling every 100ms
4. Parse and apply new events as they appear

### Implementation

- Add `--replay` flag to `sp dashboard` (takes a file path)
- Add `--speed` flag (float, default 10.0 — meaning 10x faster than real time)
- Add `--follow` flag to `sp dashboard` (takes a file path)
- Shared `_parse_ndjson_event()` and `_parse_ndjson_timestamp()` helpers in cli.py
- `cmd_dashboard_replay()` and `cmd_dashboard_follow()` functions

### Tests

- Parse valid/invalid NDJSON lines
- Replay reconstructs correct BuildState from events
- Speed=0 replays instantly
- Invalid JSON lines are silently skipped
- Follow reads existing content and picks up new lines
- Missing file exits with error

## Files to Read Before Starting

- `src/specsoloist/subscribers/ndjson.py` — NDJSON format (write side)
- `src/specsoloist/tui.py` — TUI app (from task 31b)
- `src/specsoloist/subscribers/build_state.py` — BuildState (from task 31a)

## Success Criteria

- `sp dashboard --replay test.ndjson` plays back a log in the TUI
- `sp dashboard --follow test.ndjson` tails a live log in the TUI
- `uv run python -m pytest tests/test_ndjson_replay.py` passes
- `uv run python -m pytest tests/` — all tests pass
- `uv run ruff check src/` — clean
- Animated GIF can be recorded from the replay
