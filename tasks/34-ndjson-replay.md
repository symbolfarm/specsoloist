# Task 34: `sp dashboard --replay` for NDJSON log files

**Effort**: Small

**Depends on**: Task 31b (Textual app skeleton)

## Motivation

A replay mode that feeds an NDJSON log file into the TUI at accelerated speed lets people
experience the dashboard without running an actual LLM build. Useful for:

- README demos and animated GIFs
- Conference talks / presentations
- Testing the TUI during development without burning API credits
- Sharing build logs with collaborators ("here's what happened")

## Design

```bash
sp dashboard --replay build.ndjson              # replay at 10x speed
sp dashboard --replay build.ndjson --speed 1    # real-time replay
sp dashboard --replay build.ndjson --speed 0    # instant (no delays)
```

### How it works

1. Read NDJSON file line by line
2. Parse each line as a `BuildEvent` (reconstruct from JSON)
3. Calculate delay between consecutive events from timestamps
4. Feed events into the TUI's `BuildState` at `speed` multiplier
5. When file is exhausted, show final state and wait for `q` to quit

### Implementation

- Add `--replay` flag to `sp dashboard` (takes a file path)
- Add `--speed` flag (float, default 10.0 — meaning 10x faster than real time)
- `ReplaySubscriber` or just a function that reads the file and calls
  `app.call_from_thread()` with events on a timer

### Tests

- Replay a small NDJSON file, verify all events reach the TUI
- Speed=0 replays instantly
- Invalid JSON lines are skipped with a warning

## Files to Read Before Starting

- `src/specsoloist/subscribers/ndjson.py` — NDJSON format (write side)
- `src/specsoloist/tui.py` — TUI app (from task 31b)
- `src/specsoloist/subscribers/build_state.py` — BuildState (from task 31a)

## Success Criteria

- `sp dashboard --replay test.ndjson` plays back a log in the TUI
- Animated GIF can be recorded from the replay
