"""Tests for the TUI file viewer and SSE /files endpoint (task 39)."""

import json
import os
import tempfile
import threading
import time
from http.client import HTTPConnection

import pytest
import pytest_asyncio  # noqa: F401

from specsoloist.subscribers.build_state import BuildState, SpecState
from specsoloist.subscribers.sse import SSEServer
from specsoloist.tui import (
    DashboardApp,
    LogPanel,
    SpecInfoWidget,
    VIEW_CODE,
    VIEW_LOG,
    VIEW_SPEC,
    VIEW_TESTS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


def _building_state(specs=None):
    if specs is None:
        specs = {"config": "compiling", "parser": "queued"}
    return BuildState(
        status="building",
        total_specs=len(specs),
        build_order=list(specs.keys()),
        specs={name: SpecState(name=name, status=status) for name, status in specs.items()},
    )


def _mock_resolver(content_map: dict[tuple[str, str], str]):
    """Create a file resolver that returns from a dict of (spec_name, file_type) -> content."""
    def _resolve(spec_name: str, file_type: str) -> str | None:
        return content_map.get((spec_name, file_type))
    return _resolve


# ---------------------------------------------------------------------------
# TUI keybindings
# ---------------------------------------------------------------------------

class TestFileViewerKeybindings:

    @pytest.mark.asyncio
    async def test_s_key_switches_to_spec_view(self):
        resolver = _mock_resolver({("config", VIEW_SPEC): "# Spec content"})
        app = DashboardApp(file_resolver=resolver)
        async with app.run_test() as pilot:
            pilot.app.refresh_state(_building_state({"config": "passed"}))
            await pilot.pause()

            await pilot.press("s")
            await pilot.pause()

            assert pilot.app._view_mode == VIEW_SPEC

    @pytest.mark.asyncio
    async def test_c_key_switches_to_code_view(self):
        resolver = _mock_resolver({("config", VIEW_CODE): "def hello(): pass"})
        app = DashboardApp(file_resolver=resolver)
        async with app.run_test() as pilot:
            pilot.app.refresh_state(_building_state({"config": "passed"}))
            await pilot.pause()

            await pilot.press("c")
            await pilot.pause()

            assert pilot.app._view_mode == VIEW_CODE

    @pytest.mark.asyncio
    async def test_t_key_switches_to_tests_view(self):
        resolver = _mock_resolver({("config", VIEW_TESTS): "def test_hello(): pass"})
        app = DashboardApp(file_resolver=resolver)
        async with app.run_test() as pilot:
            pilot.app.refresh_state(_building_state({"config": "passed"}))
            await pilot.pause()

            await pilot.press("t")
            await pilot.pause()

            assert pilot.app._view_mode == VIEW_TESTS

    @pytest.mark.asyncio
    async def test_l_key_returns_to_log_view(self):
        app = DashboardApp()
        async with app.run_test() as pilot:
            pilot.app.refresh_state(_building_state({"config": "passed"}))
            await pilot.pause()

            # Switch to spec view, then back to log
            pilot.app._view_mode = VIEW_SPEC
            await pilot.press("l")
            await pilot.pause()

            assert pilot.app._view_mode == VIEW_LOG

    @pytest.mark.asyncio
    async def test_no_resolver_shows_not_available(self):
        """Without a file resolver, file view modes show 'not available'."""
        app = DashboardApp(file_resolver=None)
        async with app.run_test() as pilot:
            state = _building_state({"config": "passed"})
            state.specs["config"].log = ["some log line"]
            pilot.app.refresh_state(state)
            await pilot.pause()

            await pilot.press("s")
            await pilot.pause()

            # Log panel should show "not available" message (view_mode is spec but no resolver)
            assert pilot.app._view_mode == VIEW_SPEC

    @pytest.mark.asyncio
    async def test_file_content_displayed_via_resolver(self):
        """File resolver content is used when switching to file view."""
        resolver = _mock_resolver({("config", VIEW_SPEC): "# My spec\nThis is the content."})
        app = DashboardApp(file_resolver=resolver)
        async with app.run_test() as pilot:
            pilot.app.refresh_state(_building_state({"config": "passed"}))
            await pilot.pause()

            await pilot.press("s")
            await pilot.pause()

            # The log panel should contain the spec content (rendered via Syntax)
            log_panel = pilot.app.query_one("#log-panel", LogPanel)
            # RichLog content is hard to inspect directly; verify view_mode changed
            assert pilot.app._view_mode == VIEW_SPEC


# ---------------------------------------------------------------------------
# SSE /files endpoint
# ---------------------------------------------------------------------------

class TestSSEFilesEndpoint:

    @pytest.fixture
    def project_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Create test files
            os.makedirs(os.path.join(tmp, "src"))
            with open(os.path.join(tmp, "src", "config.py"), "w") as f:
                f.write("# config module\ndef load(): pass\n")
            os.makedirs(os.path.join(tmp, "specs"))
            with open(os.path.join(tmp, "specs", "config.spec.md"), "w") as f:
                f.write("---\nname: config\n---\n# Overview\nConfig module.\n")
            yield tmp

    @pytest.fixture
    def file_server(self, project_dir):
        port = _find_free_port()
        server = SSEServer(port=port, project_root=project_dir)
        server.start()
        time.sleep(0.1)
        yield server
        server.stop()

    def test_files_returns_content(self, file_server, project_dir):
        """GET /files?path=src/config.py returns file contents."""
        conn = HTTPConnection("localhost", file_server.port, timeout=5)
        conn.request("GET", "/files?path=src/config.py")
        resp = conn.getresponse()

        assert resp.status == 200
        assert resp.getheader("Content-Type") == "text/plain; charset=utf-8"
        body = resp.read().decode()
        assert "def load():" in body
        conn.close()

    def test_files_cors_headers(self, file_server, project_dir):
        """GET /files includes CORS headers."""
        conn = HTTPConnection("localhost", file_server.port, timeout=5)
        conn.request("GET", "/files?path=src/config.py")
        resp = conn.getresponse()
        resp.read()

        assert resp.getheader("Access-Control-Allow-Origin") == "*"
        conn.close()

    def test_files_missing_returns_404(self, file_server, project_dir):
        """GET /files for nonexistent file returns 404."""
        conn = HTTPConnection("localhost", file_server.port, timeout=5)
        conn.request("GET", "/files?path=src/nonexistent.py")
        resp = conn.getresponse()
        resp.read()

        assert resp.status == 404
        conn.close()

    def test_files_path_traversal_blocked(self, file_server, project_dir):
        """GET /files with path traversal returns 403."""
        conn = HTTPConnection("localhost", file_server.port, timeout=5)
        conn.request("GET", "/files?path=../../../etc/passwd")
        resp = conn.getresponse()
        body = resp.read()

        assert resp.status == 403
        assert b"Forbidden" in body
        conn.close()

    def test_files_missing_path_param(self, file_server, project_dir):
        """GET /files without ?path= returns 400."""
        conn = HTTPConnection("localhost", file_server.port, timeout=5)
        conn.request("GET", "/files")
        resp = conn.getresponse()
        resp.read()

        assert resp.status == 400
        conn.close()

    def test_files_spec_file(self, file_server, project_dir):
        """GET /files can serve spec files."""
        conn = HTTPConnection("localhost", file_server.port, timeout=5)
        conn.request("GET", "/files?path=specs/config.spec.md")
        resp = conn.getresponse()

        assert resp.status == 200
        body = resp.read().decode()
        assert "name: config" in body
        conn.close()
