# Task 32: SSE server (`sp conduct --serve`)

**Effort**: Medium

**Depends on**: Task 28 (event emission wired up) ✅, Task 31a (BuildState model)

## Motivation

The SSE server bridges the event bus to external consumers over HTTP. Any client — a browser
dashboard, `curl`, a VS Code extension, the TUI in a remote terminal — can connect and receive
build events in real time. This is the foundation for the Spechestra web dashboard.

This is IDEAS.md §3b.

## Design Decisions (locked)

- **SSE (Server-Sent Events), not WebSocket**: SSE is simpler (HTTP GET, text/event-stream),
  unidirectional (server → client), and sufficient for monitoring. WebSocket adds bidirectional
  complexity we don't need for v1. Browsers, `curl`, and `EventSource` all support SSE natively.
- **Port**: default `localhost:4510` (mnemonic: "4 S-P ecS-O loist"). Configurable via
  `--port` flag.
- **Lifecycle**: Server starts when `sp conduct --serve` is invoked. Shuts down when the build
  completes. Optionally, `--serve --keep-alive` keeps it running after the build for late
  connectors to query the final state.
- **CORS**: Allow `*` for localhost development. The Spechestra dashboard will connect from
  a different port.
- **Endpoint**: `GET /events` — SSE stream. `GET /status` — JSON snapshot of current build
  state (for late connectors, using BuildState from task 31a).

## Dependency Decision

**Neither `starlette` nor `aiohttp` is currently installed** — they are NOT transitive deps
despite what was initially assumed. Options:

1. **stdlib `http.server.ThreadingHTTPServer`** — zero deps, ~100 lines, good enough for
   localhost. Downside: no async, manual SSE formatting, no graceful streaming shutdown.
2. **Add `aiohttp` as optional dep** — lightweight async HTTP, proper SSE support, but adds
   a dependency users might not want.
3. **Add `starlette` + `uvicorn` as optional deps** — ASGI, clean SSE via `StreamingResponse`,
   but heavier.

**Recommended: stdlib for v1.** The SSE protocol is trivial to implement manually
(`data: {json}\n\n`). A `ThreadingHTTPServer` in a background thread is sufficient for
localhost. Upgrade to aiohttp/starlette later if needed (the subscriber interface won't change).

If going stdlib: use `http.server.ThreadingHTTPServer` with custom `BaseHTTPRequestHandler`.
For SSE, set `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`,
then write `data: {json}\n\n` in a loop, reading from a `queue.Queue` per-client.

## Implementation

### New file: `src/specsoloist/subscribers/sse.py`

- `SSEServer` — wraps `ThreadingHTTPServer`, manages client connections
  - `start(port=4510)` — starts server in a background daemon thread
  - `stop()` — shuts down server
  - `broadcast(event: BuildEvent)` — push event to all connected clients
- `SSEHandler(BaseHTTPRequestHandler)` — handles HTTP requests:
  - `GET /events` — SSE stream (each event: `data: {json}\n\n`)
  - `GET /status` — JSON snapshot of BuildState
  - CORS headers on all responses
- `SSESubscriber` — EventBus subscriber that calls `server.broadcast(event)` and
  updates a `BuildState` instance (from task 31a) for the /status endpoint

### Modified: `src/specsoloist/cli.py`

- Add `--serve` flag to `sp conduct` (and `sp build`)
- Add `--port` flag (default 4510)
- Add `--keep-alive` flag
- When `--serve`: create EventBus, start SSE server, subscribe it, run build, shutdown
- Print: "SSE server listening on http://localhost:4510/events"

### Spec

Write `score/sse.spec.md` covering the SSE subscriber and server endpoints.

### Tests

- `tests/test_sse_server.py`
- Server starts and responds to `GET /status` with valid JSON
- `GET /status` includes CORS headers
- SSE stream delivers events (connect, emit event, read from stream)
- Server shuts down cleanly (stop() joins the thread)
- Multiple clients receive the same events

### Tips for Implementation

- Each SSE client gets its own `queue.Queue`. The `SSESubscriber.broadcast()` puts the event
  on every client queue. The handler's `do_GET` for `/events` blocks reading from its queue.
- When a client disconnects (broken pipe), catch the exception and remove the client's queue.
- Use `daemon=True` for the server thread so it doesn't block process exit.
- The `/status` endpoint serializes `BuildState` to JSON — reuse `BuildState` from task 31a.
  If 31a isn't done yet, a simple dict accumulator works as a stopgap.

## Files to Read Before Starting

- `src/specsoloist/events.py` — BuildEvent, EventBus
- `src/specsoloist/subscribers/ndjson.py` — subscriber pattern
- `src/specsoloist/subscribers/build_state.py` — BuildState (from task 31a, if done)
- `src/specsoloist/cli.py` — `cmd_conduct()`, how `--log-file` was wired (pattern to follow)
- `pyproject.toml` — current dependencies

## Success Criteria

- `uv run python -m pytest tests/test_sse_server.py` passes
- `uv run python -m pytest tests/` — all tests pass
- `uv run ruff check src/` — clean
- `sp conduct --serve` starts a server; `curl -N localhost:4510/events` streams events
- `curl localhost:4510/status` returns JSON
- `score/sse.spec.md` passes `sp validate`
