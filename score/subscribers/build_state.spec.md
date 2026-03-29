---
name: build_state
type: bundle
dependencies:
  - from: events.spec.md
tags:
  - observability
  - data
---

# Overview

Accumulates `BuildEvent`s into a snapshot of build progress. Pure data layer with no UI dependencies — usable by TUI, SSE endpoints, and NDJSON replay consumers.

`BuildState` is the single source of truth for all display layers. It must be fully reconstructable from its fields (no event history required), and serializable to JSON for late-joining clients.

# Types

## SpecState

Per-spec compilation state. Dataclass with fields:

- `name`: string — spec identifier
- `status`: string — one of `"queued"`, `"compiling"`, `"testing"`, `"passed"`, `"failed"`, `"fixing"`
- `duration`: optional float — total compilation time in seconds
- `input_tokens`: int (default 0) — LLM input tokens (reserved for future per-spec attribution)
- `output_tokens`: int (default 0) — LLM output tokens (reserved for future per-spec attribution)
- `error`: optional string — error message if failed
- `retries`: int (default 0) — number of fix attempts
- `log`: list of strings (default empty) — accumulated human-readable event log lines

## BuildState

Build-level state accumulator. Dataclass with fields:

- `specs`: dict mapping spec name to `SpecState`
- `build_order`: list of spec names in dependency order
- `total_specs`: int — number of specs in the build
- `specs_completed`: int — specs that finished successfully
- `specs_failed`: int — specs that failed (compile or test)
- `total_input_tokens`: int — aggregate LLM input tokens
- `total_output_tokens`: int �� aggregate LLM output tokens
- `start_time`: optional float — monotonic timestamp of build start
- `elapsed`: float — seconds since build started (set on completion)
- `status`: string — one of `"idle"`, `"building"`, `"completed"`, `"failed"`

# Functions

## BuildState.apply(event)

Apply a single `BuildEvent` to update state. This is the state machine — all state transitions flow through here.

**State transitions by event type:**

- `build.started` → status becomes `"building"`, records `total_specs` and `build_order` from event data, creates `SpecState` entries (status `"queued"`) for each spec in build order
- `build.completed` → status becomes `"completed"` (or `"failed"` if any specs failed), records elapsed time
- `build.level.started` → no state change (informational)
- `spec.compile.started` → spec status becomes `"compiling"`, appends log "Generating implementation..."
- `spec.compile.completed` → spec status becomes `"passed"`, records duration, increments `specs_completed`, appends log with duration
- `spec.compile.failed` → spec status becomes `"failed"`, records error message, increments `specs_failed`, appends log with error
- `spec.tests.started` → spec status becomes `"testing"`, appends log "Running tests..."
- `spec.tests.completed` → if `success` is false: spec status becomes `"failed"`, records error, appends "Tests failed"; if true: appends "Tests passed" (compile completion determines final status)
- `spec.fix.started` → spec status becomes `"fixing"`, increments retry count, appends log with attempt number
- `spec.fix.completed` → spec status becomes `"testing"` (fix leads to re-test), appends log "Fix applied, re-testing..."
- `llm.response` → accumulates `input_tokens` and `output_tokens` at build level
- `llm.request` → no state change (informational)
- Unknown event types → silently ignored (forward compatibility)

**Edge cases:**

- Events referencing a spec not in the build order create a new `SpecState` on the fly
- Events with `spec_name=None` are handled gracefully (attributed to a sentinel key)
- `specs_failed` only increments once per spec for test failures (not double-counted if already failed from compilation)
- Multiple specs can be in `"compiling"` status simultaneously (parallel builds)
- Fix retry cycles can repeat: `failed → fixing → testing → (passed | failed → fixing...)`

## BuildState.to_dict()

Serialize the entire state to a plain dict suitable for `json.dumps()`. All nested `SpecState` objects become dicts. No custom JSON encoder needed.

# Examples

```python
from specsoloist.events import BuildEvent, EventType
from specsoloist.subscribers.build_state import BuildState

state = BuildState()

# Build starts with 2 specs
state.apply(BuildEvent(
    event_type=EventType.BUILD_STARTED,
    data={"total_specs": 2, "build_order": ["config", "parser"]},
))
assert state.status == "building"
assert state.specs["config"].status == "queued"

# Config compiles successfully
state.apply(BuildEvent(event_type=EventType.SPEC_COMPILE_STARTED, spec_name="config"))
state.apply(BuildEvent(event_type=EventType.SPEC_COMPILE_COMPLETED, spec_name="config", data={"duration_seconds": 2.1}))
assert state.specs["config"].status == "passed"
assert state.specs_completed == 1

# Serializable for SSE /status endpoint
import json
json.dumps(state.to_dict())
```

# Verification

```python
from specsoloist.subscribers.build_state import BuildState, SpecState

# Types exist and are constructable
s = SpecState(name="test")
assert s.status == "queued"
assert s.retries == 0
assert s.log == []

b = BuildState()
assert b.status == "idle"
```

# Constraints

- No UI framework imports (no Textual, no Rich) — pure Python data layer
- Thread-safe when used from the EventBus consumer thread
- `to_dict()` output must be JSON-serializable without custom encoders
