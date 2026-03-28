---
name: events
type: bundle
tags:
  - observability
  - core
---

# Overview

Event bus for SpecSoloist build observability. Components emit `BuildEvent`s during compilation; subscribers handle them for logging, TUI display, or network streaming. The bus is thread-safe (backed by `queue.Queue`) and works with the existing `ThreadPoolExecutor` parallel builds.

The event bus is optional — when not provided, all operations behave identically to before. Zero overhead when unused.

# Types

## BuildEvent

Frozen dataclass representing a single observable event during a build.

**Fields:**
- `event_type`: string, dotted event name (e.g., `"build.started"`, `"spec.compile.completed"`)
- `timestamp`: datetime (UTC), when the event was created (default: `datetime.now(UTC)`)
- `spec_name`: optional string, the spec this event relates to (None for build-level events)
- `data`: dict, event-specific payload (default: empty dict)

## EventType

Module-level string constants for event types:

- `BUILD_STARTED = "build.started"`
- `BUILD_COMPLETED = "build.completed"`
- `BUILD_LEVEL_STARTED = "build.level.started"`
- `SPEC_COMPILE_STARTED = "spec.compile.started"`
- `SPEC_COMPILE_COMPLETED = "spec.compile.completed"`
- `SPEC_COMPILE_FAILED = "spec.compile.failed"`
- `SPEC_TESTS_STARTED = "spec.tests.started"`
- `SPEC_TESTS_COMPLETED = "spec.tests.completed"`
- `SPEC_FIX_STARTED = "spec.fix.started"`
- `SPEC_FIX_COMPLETED = "spec.fix.completed"`
- `LLM_REQUEST = "llm.request"`
- `LLM_RESPONSE = "llm.response"`

# Functions

## EventBus.__init__()

Create an event bus. Starts a background consumer thread that dispatches events to subscribers.

## EventBus.subscribe(handler)

Register a subscriber. `handler` is any callable that accepts a single `BuildEvent` argument. Subscribers are called in registration order by the consumer thread.

- Can be called before or after events start flowing
- Returns None

## EventBus.emit(event)

Publish a `BuildEvent`. Puts the event on an internal queue and returns immediately. Thread-safe — can be called from any thread (including `ThreadPoolExecutor` workers).

- If the bus is closed, the event is silently dropped
- Returns None

## EventBus.close()

Drain remaining events, dispatch them to subscribers, then stop the consumer thread. Blocks until the consumer thread joins.

- Idempotent — safe to call multiple times
- After close, further `emit()` calls are silently dropped

## EventBus context manager

`EventBus` supports `with` statement usage:
- `__enter__` returns `self`
- `__exit__` calls `close()`

# Examples

```python
from specsoloist.events import EventBus, BuildEvent, EventType

# Basic usage
with EventBus() as bus:
    received = []
    bus.subscribe(lambda e: received.append(e))

    bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED, data={"total_specs": 5}))
    bus.emit(BuildEvent(
        event_type=EventType.SPEC_COMPILE_STARTED,
        spec_name="config",
        data={"dependencies": []},
    ))

# After exiting, all events have been dispatched
assert len(received) == 2
assert received[0].event_type == "build.started"
assert received[1].spec_name == "config"
```

```python
# Thread safety — emit from multiple threads
import threading
from specsoloist.events import EventBus, BuildEvent, EventType

with EventBus() as bus:
    received = []
    bus.subscribe(lambda e: received.append(e))

    threads = []
    for i in range(10):
        t = threading.Thread(
            target=bus.emit,
            args=(BuildEvent(event_type=EventType.SPEC_COMPILE_STARTED, spec_name=f"spec_{i}"),),
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

assert len(received) == 10
```

# Verification

```python
from specsoloist.events import EventBus, BuildEvent, EventType

# BuildEvent is a frozen dataclass
e = BuildEvent(event_type=EventType.BUILD_STARTED)
assert e.event_type == "build.started"
assert e.spec_name is None
assert e.data == {}
assert e.timestamp is not None

# EventBus context manager works
with EventBus() as bus:
    assert bus is not None
```
