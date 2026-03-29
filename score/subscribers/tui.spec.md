---
name: tui
type: bundle
status: draft
description: >
  Thin bridge from the EventBus to a Textual app. Holds a BuildState and
  an optional app reference. On each event, applies it to the state and
  notifies the app via call_from_thread().
dependencies:
  - name: BuildState
    from: subscribers/build_state.spec.md
  - name: BuildEvent
    from: events.spec.md
---

# Overview

`TuiSubscriber` is a callable event-bus subscriber that maintains a `BuildState`
and optionally pushes state updates to a Textual app. No Textual import at module
level -- the app reference uses a Protocol so this module stays testable without
Textual installed.

# API

```yaml:functions
TuiApp:
  kind: class
  description: >
    Protocol for the Textual app interface. Any object with call_from_thread
    and refresh_state methods satisfies this.
  methods:
    call_from_thread:
      parameters:
        - name: callback
          type: Any
        - name: "*args"
          type: Any
      returns: None
    refresh_state:
      parameters:
        - name: state
          type: BuildState
      returns: None

TuiSubscriber:
  kind: class
  constructor:
    parameters:
      - name: app
        type: "TuiApp | None"
        default: "None"
        description: "Textual app to notify. Can be set later via the app property."
  properties:
    state:
      type: BuildState
      description: "The accumulated build state."
    app:
      type: "TuiApp | None"
      description: "The Textual app receiving updates. Settable after construction."
  methods:
    __call__:
      parameters:
        - name: event
          type: BuildEvent
      returns: None
      description: >
        Apply the event to self.state, then if app is set, call
        app.call_from_thread(app.refresh_state, self.state).
```

# Behavior

- Events are applied to the internal `BuildState` via `state.apply(event)`.
- If `app` is set, the subscriber notifies the UI thread via
  `app.call_from_thread(app.refresh_state, self.state)` after each event.
- If `app` is None, events are still accumulated silently (headless mode).
- The `app` property can be set after construction, enabling late binding
  (e.g., create subscriber, subscribe to bus, then set app once mounted).

# Verification

```python
from unittest.mock import MagicMock
from specsoloist.events import BuildEvent, EventType
from specsoloist.subscribers.tui import TuiSubscriber

sub = TuiSubscriber()
sub(BuildEvent(event_type=EventType.BUILD_STARTED, data={"total_specs": 2, "build_order": ["a", "b"]}))
assert sub.state.status == "building"

app = MagicMock()
sub.app = app
sub(BuildEvent(event_type=EventType.SPEC_COMPILE_STARTED, spec_name="a"))
app.call_from_thread.assert_called_once()
```
