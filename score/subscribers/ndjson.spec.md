---
name: ndjson
type: bundle
status: draft
description: >
  NDJSON (Newline Delimited JSON) event subscriber. Writes one JSON object
  per line to a file or stdout, enabling post-hoc analysis with jq, Datadog,
  Grafana, or any log aggregator.
dependencies:
  - name: BuildEvent
    from: events.spec.md
---

# Overview

`NdjsonSubscriber` is a callable that serializes `BuildEvent`s to NDJSON format
and writes them to any writable text stream (file, stdout, StringIO). Each event
becomes one JSON line with `event_type`, `timestamp`, `spec_name`, and all fields
from `event.data` flattened into the top level.

# API

```yaml:functions
NdjsonSubscriber:
  kind: class
  constructor:
    parameters:
      - name: file
        type: "IO[str]"
        description: "Writable text stream (open file, sys.stdout, StringIO)"
  methods:
    __call__:
      parameters:
        - name: event
          type: BuildEvent
      returns: None
      description: >
        Serialize the event as a JSON object and write it as a single line
        followed by a newline. Flushes after each write.
```

# Behavior

- Each call to `__call__` writes exactly one JSON line to the file.
- The JSON object contains `event_type`, `timestamp` (ISO 8601), `spec_name`
  (may be null), and all key-value pairs from `event.data` at the top level.
- The stream is flushed after every write so downstream consumers see events
  immediately.
- Non-serializable values in `event.data` are converted to strings via
  `json.dumps(default=str)`.

# Verification

```python
import json
from io import StringIO
from specsoloist.events import BuildEvent, EventType
from specsoloist.subscribers.ndjson import NdjsonSubscriber

buf = StringIO()
sub = NdjsonSubscriber(buf)
sub(BuildEvent(event_type=EventType.BUILD_STARTED, data={"total_specs": 3}))
line = buf.getvalue().strip()
obj = json.loads(line)
assert obj["event_type"] == "build.started"
assert obj["total_specs"] == 3
assert "timestamp" in obj
```
