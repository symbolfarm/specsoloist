# Task 32: SSE server (`sp conduct --serve`)

**Effort**: Medium

**Depends on**: Task 28 (event emission wired up)

## Motivation

The SSE server bridges the event bus to external consumers over HTTP. Any client — a browser
dashboard, `curl`, a VS Code extension, the TUI in a remote terminal — can connect and receive
build events in real time. This is the foundation for the Spechestra web dashboard.

This is IDEAS.md §3b.

## Design Decisions (locked)

- **SSE (Server-Sent Events), not WebSocket**: SSE is simpler (HTTP GET, text/event-stream),
  unidirectional (server → client), and sufficient for monitoring. WebSocket adds bidirectional
  complexity we don't need for v1. Browsers, `curl`, and `EventSource` all support SSE natively.
- **Lightweight HTTP**: Use `aiohttp` or `starlette` (already a transitive dependency via
  Pydantic AI) — agent's choice. The server is ~100 lines, not a full web framework.
- **Port**: default `localhost:4510` (mnemonic: "4 S-P ecS-O loist"). Configurable via
  `--port` flag.
- **Lifecycle**: Server starts when `sp conduct --serve` is invoked. Shuts down when the build
  completes. Optionally, `--serve --keep-alive` keeps it running after the build for late
  connectors to query the final state.
- **CORS**: Allow `*` for localhost development. The Spechestra dashboard will connect from
  a different port.
- **Endpoint**: `GET /events` — SSE stream. `GET /status` — JSON snapshot of current build
  state (for late connectors).

## Implementation

### New file: `src/specsoloist/subscribers/sse.py`

- `SSESubscriber` — receives BuildEvents, pushes to connected SSE clients
- `start_sse_server(event_bus, port)` — starts the HTTP server in a background thread
- Maintains a set of connected clients; when a client disconnects, remove it
- `GET /events` — SSE stream (each event is `data: {json}\n\n`)
- `GET /status` — returns current build state as JSON (accumulated from events)

### Modified: `src/specsoloist/cli.py`

- Add `--serve` flag to `sp conduct` (and `sp build`)
- Add `--port` flag (default 4510)
- Add `--keep-alive` flag
- When `--serve`: create EventBus, start SSE server, subscribe it, run build, shutdown

### Spec

Write `score/sse.spec.md` covering the SSE subscriber and server endpoints.

### Tests

- `tests/test_sse_server.py`
- Server starts and responds to `GET /status` with JSON
- SSE stream delivers events in order
- Multiple clients receive the same events
- Server shuts down cleanly after build completes
- CORS headers present

### Dependencies

- Evaluate whether `starlette` (already transitive) or `aiohttp` is lighter. Prefer no new
  dependency if possible.

## Files to Read Before Starting

- `src/specsoloist/events.py` — BuildEvent, EventBus
- `src/specsoloist/cli.py` — `cmd_conduct()`, how flags are parsed
- `pyproject.toml` — current dependencies (check if starlette is already available)

## Success Criteria

- `uv run python -m pytest tests/test_sse_server.py` passes
- `uv run python -m pytest tests/` — all tests pass
- `uv run ruff check src/` — clean
- `sp conduct score/ --serve` starts a server; `curl localhost:4510/events` streams events
- `score/sse.spec.md` passes `sp validate`
