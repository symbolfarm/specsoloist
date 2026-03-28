# Task 31: TUI dashboard (`sp dashboard`)

**Effort**: Large

**Depends on**: Task 28 (event emission wired up)

## Motivation

The terminal dashboard makes builds visible in real time. Open it in a second terminal pane
while working in Claude Code or your editor. It subscribes to the event bus and renders a
live view of the build: dependency graph, per-spec status, log stream, and token usage.

This is the open-source observability layer — no web server, no browser, just a terminal.

## Design Decisions (locked)

- **Textual framework**: Textual (from the Rich team) provides the TUI app framework. It's
  a natural fit — SpecSoloist already depends on Rich, and Textual extends it with widgets,
  layouts, and reactive updates.
- **Read-only for v1**: The dashboard observes but does not control. No pause/cancel/reprioritize
  buttons yet. Those come in a future task once the command channel architecture is designed.
- **Connection model**: `sp dashboard` connects to a running `sp conduct --serve` via SSE
  (task 32). Alternatively, `sp conduct --tui` runs the build *inside* the TUI app directly
  (event bus is in-process). Both modes use the same Textual app — the difference is where
  events come from.
- **Graceful degradation**: If no build is running, the dashboard shows the last known state
  from the manifest/log file.

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  SpecSoloist Dashboard               ■ Build in progress │
├──────────────────────┬──────────────────────────────────┤
│  Dependency Graph    │  Spec Detail                     │
│                      │                                  │
│  ○ config            │  Name: parser                    │
│  ○ resolver          │  Status: Testing...              │
│  ● parser ←          │  Duration: 12.3s                 │
│  ◌ manifest          │  Tokens: 1,840 in / 3,200 out   │
│  ◌ compiler          │                                  │
│  ◌ runner            │  ┌─ Log ──────────────────────┐  │
│  ◌ core              │  │ Generating implementation...│  │
│                      │  │ Writing src/parser.py       │  │
│  ○ = done            │  │ Running tests...            │  │
│  ● = in progress     │  │ 46/46 passed               │  │
│  ◌ = queued          │  └────────────────────────────┘  │
├──────────────────────┴──────────────────────────────────┤
│  Tokens: 12,400 in / 28,800 out    Cost: ~$0.04        │
│  Progress: 3/13 specs    Elapsed: 45s                   │
└─────────────────────────────────────────────────────────┘
```

## Implementation

### New file: `src/specsoloist/tui.py`

Textual app with:
- `DashboardApp(App)` — main application
- `DependencyGraphWidget` — left panel, shows specs with status icons
- `SpecDetailWidget` — right panel, shows selected spec's details and log
- `StatusBar` — bottom bar with aggregate stats (tokens, cost, progress, elapsed)
- Keyboard: `q` quit, `j/k` or arrow keys to navigate specs, `enter` to select

### New file: `src/specsoloist/subscribers/tui.py`

- `TuiSubscriber` — receives `BuildEvent`s and posts them to the Textual app's message queue
  via `app.call_from_thread()` (Textual's thread-safe bridge)

### Modified: `src/specsoloist/cli.py`

- Add `sp dashboard` subcommand
- `--tui` flag on `sp conduct` (runs build inside the TUI)
- `sp dashboard` with no arguments connects to `--serve` endpoint (task 32 dependency — for
  now, `--tui` mode is the primary path)

### Spec

Write `score/tui.spec.md` — the existing `score/ui.spec.md` covers the Rich console helpers;
this is a separate concern (Textual app vs Rich utilities).

### Tests

- `tests/test_tui.py`
- `TuiSubscriber` correctly translates BuildEvents into Textual messages
- `DashboardApp` can be instantiated (Textual has `app.run_test()` for headless testing)
- Status transitions: queued → compiling → testing → passed/failed update correctly
- Token accumulation in status bar

### Dependencies

- Add `textual>=0.50` to `pyproject.toml` (it already depends on `rich`)

## Files to Read Before Starting

- `src/specsoloist/ui.py` — existing Rich UI (separate concern but informs style)
- `src/specsoloist/events.py` — BuildEvent, EventBus
- `src/specsoloist/resolver.py` — DependencyGraph (for rendering the graph widget)
- Textual docs: https://textual.textualize.io/

## Success Criteria

- `uv run python -m pytest tests/test_tui.py` passes
- `uv run python -m pytest tests/` — all tests pass
- `uv run ruff check src/` — clean
- `sp conduct score/ --tui` shows a live-updating terminal dashboard
- `score/tui.spec.md` passes `sp validate`
