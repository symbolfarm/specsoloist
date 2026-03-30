"""Tests for SSE server and subscriber."""

import json
import queue
import threading
import time
from http.client import HTTPConnection

import pytest

from specsoloist.events import BuildEvent, EventBus, EventType
from specsoloist.subscribers.build_state import BuildState
from specsoloist.subscribers.sse import SSEServer, SSESubscriber


def _find_free_port():
    """Find an available port for testing."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


@pytest.fixture
def sse_server():
    """Create and start an SSE server on a random port, stop after test."""
    port = _find_free_port()
    server = SSEServer(port=port)
    server.start()
    # Give the server a moment to start
    time.sleep(0.1)
    yield server
    server.stop()


class TestSSEServer:
    """Tests for SSEServer HTTP endpoints."""

    def test_status_returns_json(self, sse_server):
        """GET /status returns valid JSON with BuildState fields."""
        conn = HTTPConnection("localhost", sse_server.port, timeout=5)
        conn.request("GET", "/status")
        resp = conn.getresponse()

        assert resp.status == 200
        assert resp.getheader("Content-Type") == "application/json"

        body = json.loads(resp.read().decode())
        assert "status" in body
        assert "specs" in body
        assert body["status"] == "idle"
        conn.close()

    def test_status_cors_headers(self, sse_server):
        """GET /status includes CORS headers."""
        conn = HTTPConnection("localhost", sse_server.port, timeout=5)
        conn.request("GET", "/status")
        resp = conn.getresponse()
        resp.read()

        assert resp.getheader("Access-Control-Allow-Origin") == "*"
        conn.close()

    def test_options_cors_preflight(self, sse_server):
        """OPTIONS request returns CORS headers for preflight."""
        conn = HTTPConnection("localhost", sse_server.port, timeout=5)
        conn.request("OPTIONS", "/events")
        resp = conn.getresponse()
        resp.read()

        assert resp.status == 200
        assert resp.getheader("Access-Control-Allow-Origin") == "*"
        assert "GET" in resp.getheader("Access-Control-Allow-Methods")
        conn.close()

    def test_404_for_unknown_path(self, sse_server):
        """Unknown paths return 404."""
        conn = HTTPConnection("localhost", sse_server.port, timeout=5)
        conn.request("GET", "/unknown")
        resp = conn.getresponse()
        resp.read()

        assert resp.status == 404
        conn.close()

    def test_events_stream_delivers_events(self, sse_server):
        """SSE stream delivers broadcast events."""
        received = []
        connected = threading.Event()

        def _read_stream():
            conn = HTTPConnection("localhost", sse_server.port, timeout=5)
            conn.request("GET", "/events")
            resp = conn.getresponse()
            connected.set()
            buf = b""
            while len(received) < 2:
                chunk = resp.read(1)
                if not chunk:
                    break
                buf += chunk
                if buf.endswith(b"\n\n"):
                    for line in buf.decode().strip().split("\n"):
                        if line.startswith("data: "):
                            received.append(json.loads(line[6:]))
                    buf = b""

        reader = threading.Thread(target=_read_stream, daemon=True)
        reader.start()

        # Wait for client to connect
        connected.wait(timeout=2)
        time.sleep(0.1)

        # Broadcast two events
        sse_server.broadcast(json.dumps({"event_type": "test.one", "msg": "hello"}))
        sse_server.broadcast(json.dumps({"event_type": "test.two", "msg": "world"}))

        reader.join(timeout=3)

        assert len(received) == 2
        assert received[0]["event_type"] == "test.one"
        assert received[1]["msg"] == "world"

    def test_multiple_clients_receive_same_events(self, sse_server):
        """Multiple SSE clients all receive the same broadcast."""
        results = {0: [], 1: []}
        connected = threading.Barrier(3, timeout=5)  # 2 readers + main

        def _read_stream(idx):
            conn = HTTPConnection("localhost", sse_server.port, timeout=5)
            conn.request("GET", "/events")
            resp = conn.getresponse()
            connected.wait()
            buf = b""
            while len(results[idx]) < 1:
                chunk = resp.read(1)
                if not chunk:
                    break
                buf += chunk
                if buf.endswith(b"\n\n"):
                    for line in buf.decode().strip().split("\n"):
                        if line.startswith("data: "):
                            results[idx].append(json.loads(line[6:]))
                    buf = b""

        t0 = threading.Thread(target=_read_stream, args=(0,), daemon=True)
        t1 = threading.Thread(target=_read_stream, args=(1,), daemon=True)
        t0.start()
        t1.start()

        connected.wait()
        time.sleep(0.1)

        sse_server.broadcast(json.dumps({"event_type": "multi.test"}))

        t0.join(timeout=3)
        t1.join(timeout=3)

        assert len(results[0]) == 1
        assert len(results[1]) == 1
        assert results[0][0]["event_type"] == "multi.test"
        assert results[1][0]["event_type"] == "multi.test"

    def test_server_stops_cleanly(self, sse_server):
        """Server.stop() shuts down without hanging."""
        # The fixture will call stop() — just verify we can start/stop
        sse_server.stop()

        # Should be able to start again on same port
        sse_server.start()
        time.sleep(0.1)

        conn = HTTPConnection("localhost", sse_server.port, timeout=5)
        conn.request("GET", "/status")
        resp = conn.getresponse()
        assert resp.status == 200
        conn.close()

    def test_status_reflects_build_state(self, sse_server):
        """GET /status reflects state changes from applied events."""
        sse_server.state.apply(BuildEvent(
            event_type=EventType.BUILD_STARTED,
            data={"total_specs": 3, "build_order": ["a", "b", "c"]},
        ))

        conn = HTTPConnection("localhost", sse_server.port, timeout=5)
        conn.request("GET", "/status")
        resp = conn.getresponse()
        body = json.loads(resp.read().decode())

        assert body["status"] == "building"
        assert body["total_specs"] == 3
        assert "a" in body["specs"]
        conn.close()


class TestSSESubscriber:
    """Tests for SSESubscriber integration with EventBus."""

    def test_subscriber_updates_state_and_broadcasts(self):
        """SSESubscriber applies events to BuildState and broadcasts."""
        port = _find_free_port()
        server = SSEServer(port=port)
        server.start()
        time.sleep(0.1)

        try:
            subscriber = SSESubscriber(server)

            # Connect a client
            received = []
            connected = threading.Event()

            def _read():
                conn = HTTPConnection("localhost", port, timeout=5)
                conn.request("GET", "/events")
                resp = conn.getresponse()
                connected.set()
                buf = b""
                while len(received) < 1:
                    chunk = resp.read(1)
                    if not chunk:
                        break
                    buf += chunk
                    if buf.endswith(b"\n\n"):
                        for line in buf.decode().strip().split("\n"):
                            if line.startswith("data: "):
                                received.append(json.loads(line[6:]))
                        buf = b""

            reader = threading.Thread(target=_read, daemon=True)
            reader.start()
            connected.wait(timeout=2)
            time.sleep(0.1)

            # Fire event through subscriber
            event = BuildEvent(
                event_type=EventType.BUILD_STARTED,
                data={"total_specs": 5, "build_order": ["x", "y"]},
            )
            subscriber(event)

            reader.join(timeout=3)

            # State updated
            assert server.state.status == "building"
            assert server.state.total_specs == 5

            # Client received event
            assert len(received) == 1
            assert received[0]["event_type"] == EventType.BUILD_STARTED
        finally:
            server.stop()

    def test_subscriber_with_event_bus(self):
        """SSESubscriber works when wired into an EventBus."""
        port = _find_free_port()
        server = SSEServer(port=port)
        server.start()
        time.sleep(0.1)

        try:
            bus = EventBus()
            subscriber = SSESubscriber(server)
            bus.subscribe(subscriber)

            bus.emit(BuildEvent(
                event_type=EventType.BUILD_INIT,
                data={"command": "sp conduct --serve"},
            ))

            # Give the bus consumer thread time to process
            time.sleep(0.2)

            assert server.state.status == "initializing"
            assert server.state.command == "sp conduct --serve"

            bus.close()
        finally:
            server.stop()
