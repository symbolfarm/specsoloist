# Task 31: TUI dashboard (`sp dashboard`)

**Effort**: Large — broken into subtasks 31a–31d below

**Depends on**: Task 28 (event emission wired up) ✅

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
- **Connection model**: `sp conduct --tui` runs the build *inside* the TUI app directly
  (event bus is in-process). `sp dashboard` connects to a running `sp conduct --serve` via SSE
  (task 32). Both modes use the same Textual app — the difference is where events come from.
- **Graceful degradation**: If no build is running, the dashboard shows "waiting for build"
  or replays the last NDJSON log file.

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

---

## Subtask 31a: BuildState model + TuiSubscriber

**Effort**: Small

The data layer that accumulates events into displayable state. No Textual dependency — pure
Python, fully testable.

### New file: `src/specsoloist/subscribers/build_state.py`

`BuildState` — a mutable model that absorbs BuildEvents and maintains current state:

```python
@dataclass
class SpecState:
    name: str
    status: str  # "queued" | "compiling" | "testing" | "passed" | "failed" | "fixing"
    duration: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None

@dataclass
class BuildState:
    specs: dict[str, SpecState]   # name -> state
    build_order: list[str]
    total_specs: int = 0
    specs_completed: int = 0
    specs_failed: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    start_time: float | None = None
    elapsed: float = 0.0
    status: str = "idle"  # "idle" | "building" | "completed" | "failed"

    def apply(self, event: BuildEvent) -> None: ...
```

`BuildState.apply(event)` is a pure state machine — given any event, update the state.
This is the single source of truth for all display layers (TUI, SSE /status, NDJSON replay).

**State machine edge cases to handle:**
- **Fix retry loop**: `spec.fix.started` → `spec.fix.completed` can happen multiple times
  per spec. The status should cycle: `failed → fixing → testing → (passed | failed → fixing...)`.
  Track retry count per spec.
- **Parallel builds**: Multiple specs can be `compiling` simultaneously. `specs_completed`
  should only increment on `spec.compile.completed`, not `spec.tests.completed`.
- **LLM tokens**: `llm.response` events don't carry `spec_name` (they fire from the compiler,
  which doesn't know the spec context). Token attribution to specs requires correlating by
  timing — or accept that token totals are build-level only for v1.
- **Late joiners**: A client connecting mid-build needs the full current state, not just
  future events. `BuildState` must be fully reconstructable from its fields (no event history
  required). This is what the SSE `/status` endpoint serves.
- **Unknown events**: `apply()` should silently ignore event types it doesn't recognize,
  for forward compatibility.

### New file: `src/specsoloist/subscribers/tui.py`

`TuiSubscriber` — thin bridge from EventBus to Textual:
- Holds a `BuildState` and a reference to the Textual app
- On each event: `self.state.apply(event)`, then `app.call_from_thread(app.refresh_state, self.state)`
- `app.call_from_thread()` is Textual's thread-safe bridge to the UI thread

### Tests: `tests/test_build_state.py`

- `BuildState.apply(BUILD_STARTED)` sets status to "building", records total_specs
- `BuildState.apply(SPEC_COMPILE_STARTED)` sets spec status to "compiling"
- `BuildState.apply(SPEC_COMPILE_COMPLETED)` sets spec to "passed", increments completed
- `BuildState.apply(SPEC_COMPILE_FAILED)` sets spec to "failed", records error
- `BuildState.apply(LLM_RESPONSE)` accumulates tokens
- Full event sequence produces expected final state
- `TuiSubscriber` calls `app.call_from_thread` (mock app)

### Success Criteria

- `tests/test_build_state.py` passes
- No Textual import required — pure data layer
- `BuildState` can be serialized to JSON (for /status endpoint in task 32)

---

## Subtask 31b: Textual app skeleton + spec list widget

**Effort**: Medium

The minimal Textual app that can display a list of specs with status indicators.

### New dependency: `textual>=0.50` in `pyproject.toml`

### New file: `src/specsoloist/tui.py`

- `DashboardApp(App)` — main Textual application
- `SpecListWidget(Widget)` — left panel, renders `BuildState.specs` as a selectable list
  with status icons (○ done, ● in progress, ◌ queued, ✖ failed)
- `StatusBar(Static)` — bottom bar with aggregate stats
- Keyboard: `q` quit, arrow keys navigate spec list
- `app.refresh_state(state: BuildState)` — called from `TuiSubscriber` to update display

### Tests: `tests/test_tui.py`

- Use Textual's `app.run_test()` for headless testing
- App launches and shows "waiting for build" initially
- After feeding a BUILD_STARTED event, spec list populates
- Status icons update correctly on state changes

### Success Criteria

- `sp conduct score/ --tui` launches the TUI (build runs, specs appear with status updates)
- App exits cleanly when build completes or user presses `q`

---

## Subtask 31c: Spec detail panel

**Effort**: Small–Medium

The right panel that shows details for the selected spec.

### In `src/specsoloist/tui.py`

- `SpecDetailWidget(Widget)` — shows name, status, duration, token counts, error message
- `LogPanel(Widget)` — scrollable log of events for the selected spec
  (accumulated from events where `spec_name` matches)
- Wire selection: clicking/navigating to a spec in the list updates the detail panel

### Tests

- Selecting a spec updates the detail panel content
- Log panel scrolls and accumulates events

---

## Subtask 31d: CLI integration + `sp dashboard` command

**Effort**: Small

### Modified: `src/specsoloist/cli.py`

- Add `--tui` flag to `sp conduct` and `sp build`
- When `--tui`: create EventBus, subscribe TuiSubscriber, run build in background thread
  while Textual app runs in foreground
- Add `sp dashboard` subcommand (connects to SSE endpoint — deferred until task 32 is done;
  for now, `--tui` is the primary path)

### Tests

- `sp conduct --tui` flag is parsed correctly
- `sp dashboard` prints helpful message when no server is running

---

## Spec

Write `score/tui.spec.md` covering BuildState + the Textual app. The existing
`score/ui.spec.md` covers Rich console helpers — this is a separate concern.

## Files to Read Before Starting

- `src/specsoloist/events.py` — BuildEvent, EventBus, EventType
- `src/specsoloist/subscribers/ndjson.py` — subscriber pattern to follow
- `src/specsoloist/ui.py` — existing Rich UI (style reference)
- `src/specsoloist/resolver.py` — DependencyGraph (for rendering order)
- Textual docs: https://textual.textualize.io/
