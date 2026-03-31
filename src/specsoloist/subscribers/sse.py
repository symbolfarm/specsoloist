"""SSE (Server-Sent Events) subscriber and HTTP server.

Bridges the EventBus to external HTTP consumers. Any client — browser,
curl, VS Code extension — can connect to /events for real-time build
events or /status for a JSON snapshot of current build state.

GET /files?path=<relative> serves file contents (text/plain) for the
TUI file viewer in remote mode. A path traversal guard ensures only files
under the project root are served.

Uses stdlib http.server (zero dependencies). Thread-safe via per-client
queue.Queue instances.
"""

from __future__ import annotations

import json
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..events import BuildEvent
from .build_state import BuildState


class SSEServer:
    """HTTP server that streams build events via SSE.

    Manages per-client queues and broadcasts events to all connected
    clients. Runs in a daemon thread.
    """

    def __init__(self, port: int = 4510, project_root: str | None = None) -> None:
        """Initialize the SSE server.

        Args:
            port: Port to listen on (default 4510).
            project_root: Root directory for file serving (path traversal guard).
        """
        self.port = port
        self.project_root = os.path.realpath(project_root or os.getcwd())
        self.state = BuildState()
        self._clients: list[queue.Queue[str | None]] = []
        self._clients_lock = threading.Lock()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the HTTP server in a background daemon thread."""
        server_ref = self

        class Handler(BaseHTTPRequestHandler):
            """HTTP request handler for SSE and status endpoints."""

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if parsed.path == "/events":
                    self._handle_events()
                elif parsed.path == "/status":
                    self._handle_status()
                elif parsed.path == "/files":
                    self._handle_files(parsed)
                else:
                    self.send_error(404)

            def do_OPTIONS(self) -> None:  # noqa: N802
                self.send_response(200)
                self._send_cors_headers()
                self.end_headers()

            def _send_cors_headers(self) -> None:
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

            def _handle_events(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self._send_cors_headers()
                self.end_headers()

                client_queue: queue.Queue[str | None] = queue.Queue()
                with server_ref._clients_lock:
                    server_ref._clients.append(client_queue)

                try:
                    while True:
                        data = client_queue.get()
                        if data is None:
                            # Server shutting down
                            break
                        self.wfile.write(f"data: {data}\n\n".encode())
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                finally:
                    with server_ref._clients_lock:
                        if client_queue in server_ref._clients:
                            server_ref._clients.remove(client_queue)

            def _handle_status(self) -> None:
                body = json.dumps(server_ref.state.to_dict(), default=str)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body.encode())

            def _handle_files(self, parsed) -> None:
                qs = parse_qs(parsed.query)
                rel_path = qs.get("path", [None])[0]
                if not rel_path:
                    self.send_error(400, "Missing ?path= parameter")
                    return

                # Path traversal guard
                requested = os.path.realpath(
                    os.path.join(server_ref.project_root, rel_path)
                )
                if not requested.startswith(server_ref.project_root + os.sep):
                    self.send_response(403)
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(b"Forbidden: path traversal blocked")
                    return

                if not os.path.isfile(requested):
                    self.send_error(404, "File not found")
                    return

                try:
                    with open(requested, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except OSError:
                    self.send_error(500, "Could not read file")
                    return

                body = content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                # Suppress default stderr logging
                pass

        self._server = ThreadingHTTPServer(("localhost", self.port), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True, name="sse-server"
        )
        self._thread.start()

    def stop(self) -> None:
        """Shut down the server and disconnect all clients."""
        if self._server is not None:
            # Signal all clients to disconnect
            with self._clients_lock:
                for client_queue in self._clients:
                    client_queue.put(None)
                self._clients.clear()
            self._server.shutdown()
            if self._thread is not None:
                self._thread.join(timeout=5)
            self._server = None
            self._thread = None

    def broadcast(self, data: str) -> None:
        """Send serialized event data to all connected SSE clients.

        Args:
            data: JSON string to broadcast.
        """
        with self._clients_lock:
            dead: list[queue.Queue[str | None]] = []
            for client_queue in self._clients:
                try:
                    client_queue.put_nowait(data)
                except queue.Full:
                    dead.append(client_queue)
            for q in dead:
                self._clients.remove(q)


class SSESubscriber:
    """EventBus subscriber that broadcasts events via SSE and maintains BuildState."""

    def __init__(self, server: SSEServer) -> None:
        """Initialize with an SSEServer instance.

        Args:
            server: The SSE server to broadcast events through.
        """
        self._server = server

    def __call__(self, event: BuildEvent) -> None:
        """Serialize event to JSON, update BuildState, and broadcast."""
        self._server.state.apply(event)

        record = {
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "spec_name": event.spec_name,
            **event.data,
        }
        self._server.broadcast(json.dumps(record, default=str))
