# Task 27: Event bus and BuildEvent model

**Effort**: Medium

## Motivation

SpecSoloist currently has zero runtime observability. A `compile_project()` call blocks for
seconds to minutes behind a Rich spinner, with no intermediate progress. The event bus is the
foundation for all observability work: TUI dashboard, NDJSON logs, SSE server, and token
tracking are all *consumers* of the same event stream.

The event bus is a simple publish-subscribe system. Components emit `BuildEvent`s; subscribers
handle them. The bus itself is thread-safe (backed by `queue.Queue`) so it works with the
existing `ThreadPoolExecutor` in `compile_project` without any async rewrite.

## Design Decisions (locked)

- **Thread-safe queue**: `queue.Queue` with a dedicated consumer thread that dispatches to
  subscribers sequentially. Producers (any thread) call `emit()` which puts the event on the
  queue and returns immediately. This avoids async contamination of the core.
- **Injection, not singleton**: The `EventBus` is passed to `SpecSoloistCore.__init__()` and
  `SpecConductor.__init__()` as an optional parameter (default `None`). When `None`, no events
  are emitted — zero overhead for users who don't need observability.
- **Dataclass events**: `BuildEvent` is a frozen dataclass with `timestamp`, `event_type`,
  `spec_name` (optional), and `data` (dict). Event types use dotted names: `build.started`,
  `spec.compile.started`, etc.
- **Subscriber protocol**: `Callable[[BuildEvent], None]`. Subscribers are plain functions or
  objects with `__call__`. No base class required.
- **Graceful shutdown**: `EventBus.close()` drains the queue and joins the consumer thread.
  Used as a context manager (`with EventBus() as bus:`).

## Spec

Write `score/events.spec.md` covering:

- `BuildEvent` dataclass: `timestamp` (datetime), `event_type` (str), `spec_name` (str | None),
  `data` (dict)
- `EventBus` class: `subscribe(handler)`, `emit(event)`, `close()`, context manager protocol
- Event type constants (strings): `build.started`, `build.completed`, `build.level.started`,
  `spec.compile.started`, `spec.compile.completed`, `spec.compile.failed`, `spec.tests.started`,
  `spec.tests.completed`, `spec.fix.started`, `spec.fix.completed`, `llm.request`, `llm.response`
- Thread safety guarantees

## Implementation

### New file: `src/specsoloist/events.py`

- `BuildEvent` frozen dataclass
- `EventBus` class with `queue.Queue`, consumer thread, subscriber list
- Module-level event type constants (or an enum — agent's choice)

### Modified files

- `src/specsoloist/core.py` — accept optional `event_bus` parameter in `__init__`; store as
  `self._event_bus`. Add a `_emit(event_type, spec_name, **data)` helper that no-ops when bus
  is None. No emission points yet (task 28).
- `src/spechestra/conductor.py` — same: accept optional `event_bus`, pass through to core.

### Tests

- `tests/test_events.py`
- EventBus subscribes a handler, emits events, handler receives them in order
- Thread safety: emit from multiple threads, all events received
- Context manager: events drain on `__exit__`
- No-op when bus is None (core/conductor still work without it)

## Files to Read Before Starting

- `src/specsoloist/core.py` — `__init__` signature, `compile_project`, `_compile_single_spec`
- `src/spechestra/conductor.py` — `__init__` signature, `build`
- `src/specsoloist/ui.py` — current output patterns (for future subscriber reference)

## Success Criteria

- `uv run python -m pytest tests/test_events.py` passes
- `uv run python -m pytest tests/` — all existing tests still pass (no regressions)
- `uv run ruff check src/` — clean
- `score/events.spec.md` passes `sp validate`
- EventBus can be instantiated, subscribed to, and emitted from without importing anything else
