---
name: sse
type: bundle
status: draft
description: >
  SSE (Server-Sent Events) subscriber and HTTP server. Bridges the EventBus to
  external HTTP consumers via /events (SSE stream) and /status (JSON snapshot).
  Uses stdlib http.server — zero external dependencies.
dependencies:
  - name: BuildEvent
    from: events.spec.md
  - name: BuildState
    from: subscribers/build_state.spec.md
---

# Overview

`SSEServer` runs a lightweight HTTP server in a daemon thread. It serves two
endpoints: `GET /events` streams build events as SSE (`data: {json}\n\n`), and
`GET /status` returns the current `BuildState` as a JSON snapshot. Each connected
SSE client gets its own `queue.Queue`; `broadcast()` pushes to all clients.

`SSESubscriber` is the EventBus-compatible callable that applies events to the
server's `BuildState` and broadcasts the serialized event to all SSE clients.

# API

```yaml:functions
SSEServer:
  kind: class
  constructor:
    parameters:
      - name: port
        type: int
        default: 4510
        description: "Port to listen on"
  properties:
    port:
      type: int
      description: "Configured port number"
    state:
      type: BuildState
      description: "Current build state, served by /status"
  methods:
    start:
      parameters: []
      returns: None
      description: >
        Start the HTTP server in a background daemon thread. The server
        handles requests on localhost:{port}.
    stop:
      parameters: []
      returns: None
      description: >
        Signal all connected SSE clients to disconnect, shut down the
        HTTP server, and join the server thread.
    broadcast:
      parameters:
        - name: data
          type: str
          description: "JSON string to send to all connected SSE clients"
      returns: None
      description: >
        Push data to every connected client's queue. Removes clients
        whose queues are full (backpressure).

SSESubscriber:
  kind: class
  constructor:
    parameters:
      - name: server
        type: SSEServer
        description: "The SSE server to broadcast events through"
  methods:
    __call__:
      parameters:
        - name: event
          type: BuildEvent
      returns: None
      description: >
        Apply the event to the server's BuildState, serialize it to JSON,
        and broadcast to all connected SSE clients.
```

# Behavior

## HTTP Endpoints

- `GET /events` — SSE stream. Response headers: `Content-Type: text/event-stream`,
  `Cache-Control: no-cache`, `Connection: keep-alive`, plus CORS headers. Each
  event is sent as `data: {json}\n\n`. The connection stays open until the client
  disconnects or the server shuts down.
- `GET /status` — JSON snapshot of the current `BuildState`. Response header:
  `Content-Type: application/json`, plus CORS headers.
- `OPTIONS` on any path — returns CORS preflight headers.
- All other paths return 404.

## CORS Headers

All responses include:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type`

## Client Management

- Each SSE client gets its own `queue.Queue`. On connect, the queue is added to a
  client list; on disconnect (broken pipe), the queue is removed.
- `broadcast()` pushes to all client queues. If a queue is full, the client is
  removed (backpressure).
- On `stop()`, all client queues receive `None` as a sentinel, causing the handler
  loop to exit cleanly.

## SSESubscriber

- Applies the event to `server.state` via `BuildState.apply()`.
- Serializes the event to JSON using the same format as `NdjsonSubscriber`:
  `event_type`, `timestamp` (ISO 8601), `spec_name`, plus all `event.data` fields
  flattened at the top level.

# Verification

```python
import json
import time
import threading
from http.client import HTTPConnection
from specsoloist.events import BuildEvent, EventType
from specsoloist.subscribers.sse import SSEServer, SSESubscriber

# Start server on a free port
import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("localhost", 0))
    port = s.getsockname()[1]

server = SSEServer(port=port)
server.start()
time.sleep(0.1)

# /status returns JSON
conn = HTTPConnection("localhost", port, timeout=5)
conn.request("GET", "/status")
resp = conn.getresponse()
body = json.loads(resp.read().decode())
assert body["status"] == "idle"
assert resp.getheader("Access-Control-Allow-Origin") == "*"
conn.close()

# SSESubscriber updates state
sub = SSESubscriber(server)
sub(BuildEvent(event_type=EventType.BUILD_STARTED, data={"total_specs": 3, "build_order": ["a"]}))
assert server.state.status == "building"

server.stop()
```
