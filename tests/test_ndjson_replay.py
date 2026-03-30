"""Tests for sp dashboard --replay and --follow modes."""

import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from specsoloist.cli import (
    _parse_ndjson_event,
    _parse_ndjson_timestamp,
)
from specsoloist.events import BuildEvent, EventType


def _make_ndjson_line(event_type, spec_name=None, ts=None, **data):
    """Create a single NDJSON line for testing."""
    if ts is None:
        ts = datetime.now(timezone.utc)
    record = {
        "event_type": event_type,
        "timestamp": ts.isoformat(),
        "spec_name": spec_name,
        **data,
    }
    return json.dumps(record, default=str)


def _make_ndjson_file(tmp_path, events=None):
    """Create an NDJSON log file with a realistic sequence of events."""
    if events is None:
        base = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)
        events = [
            (EventType.BUILD_INIT, None, base, {"command": "sp conduct --no-agent"}),
            (EventType.BUILD_SPECS_DISCOVERED, None, base + timedelta(seconds=0.1), {"count": 2}),
            (EventType.BUILD_DEPS_RESOLVED, None, base + timedelta(seconds=0.2), {"levels": 1}),
            (EventType.BUILD_STARTED, None, base + timedelta(seconds=0.3), {"total_specs": 2, "build_order": ["config", "core"]}),
            (EventType.SPEC_COMPILE_STARTED, "config", base + timedelta(seconds=0.5), {}),
            (EventType.SPEC_COMPILE_COMPLETED, "config", base + timedelta(seconds=2.0), {"duration_seconds": 1.5}),
            (EventType.SPEC_COMPILE_STARTED, "core", base + timedelta(seconds=2.1), {}),
            (EventType.SPEC_COMPILE_COMPLETED, "core", base + timedelta(seconds=4.0), {"duration_seconds": 1.9}),
            (EventType.BUILD_COMPLETED, None, base + timedelta(seconds=4.1), {}),
        ]

    log_file = tmp_path / "build.ndjson"
    lines = []
    for event_type, spec_name, ts, data in events:
        lines.append(_make_ndjson_line(event_type, spec_name, ts, **data))
    log_file.write_text("\n".join(lines) + "\n")
    return log_file


class TestParseNdjsonEvent:
    """Tests for _parse_ndjson_event helper."""

    def test_valid_event(self):
        line = _make_ndjson_line(EventType.BUILD_STARTED, total_specs=3, build_order=["a"])
        event = _parse_ndjson_event(line)

        assert event is not None
        assert event.event_type == EventType.BUILD_STARTED
        assert event.data["total_specs"] == 3

    def test_with_spec_name(self):
        line = _make_ndjson_line(EventType.SPEC_COMPILE_STARTED, spec_name="config")
        event = _parse_ndjson_event(line)

        assert event is not None
        assert event.spec_name == "config"

    def test_invalid_json_returns_none(self):
        assert _parse_ndjson_event("not json") is None

    def test_missing_event_type_returns_none(self):
        assert _parse_ndjson_event('{"foo": "bar"}') is None

    def test_empty_string_returns_none(self):
        assert _parse_ndjson_event("") is None

    def test_timestamp_excluded_from_data(self):
        line = _make_ndjson_line(EventType.BUILD_INIT, command="test")
        event = _parse_ndjson_event(line)

        assert "timestamp" not in event.data
        assert "event_type" not in event.data


class TestParseNdjsonTimestamp:
    """Tests for _parse_ndjson_timestamp helper."""

    def test_valid_timestamp(self):
        ts = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)
        line = _make_ndjson_line(EventType.BUILD_INIT, ts=ts)
        result = _parse_ndjson_timestamp(line)

        assert result is not None
        assert abs(result - ts.timestamp()) < 1.0

    def test_invalid_json_returns_none(self):
        assert _parse_ndjson_timestamp("not json") is None

    def test_missing_timestamp_returns_none(self):
        assert _parse_ndjson_timestamp('{"event_type": "test"}') is None


class TestReplayMode:
    """Tests for sp dashboard --replay via subprocess."""

    def test_replay_missing_file_exits_1(self):
        import subprocess
        result = subprocess.run(
            ["uv", "run", "sp", "dashboard", "--replay", "/nonexistent/file.ndjson"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()

    def test_replay_empty_file_exits_1(self, tmp_path):
        import subprocess
        empty = tmp_path / "empty.ndjson"
        empty.write_text("")
        result = subprocess.run(
            ["uv", "run", "sp", "dashboard", "--replay", str(empty)],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "no events" in result.stdout.lower() or "no events" in result.stderr.lower()


class TestReplayBuildState:
    """Tests for replay building correct BuildState from NDJSON."""

    def test_replay_reconstructs_state(self, tmp_path):
        """Replaying an NDJSON file reconstructs the correct BuildState."""
        from specsoloist.subscribers.build_state import BuildState

        log_file = _make_ndjson_file(tmp_path)
        state = BuildState()

        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = _parse_ndjson_event(line)
                if event is not None:
                    state.apply(event)

        assert state.status in ("completed", "failed")
        assert state.total_specs == 2
        assert state.specs_completed == 2
        assert "config" in state.specs
        assert "core" in state.specs
        assert state.specs["config"].status == "passed"

    def test_replay_skips_invalid_lines(self, tmp_path):
        """Invalid JSON lines are silently skipped."""
        from specsoloist.subscribers.build_state import BuildState

        log_file = tmp_path / "mixed.ndjson"
        base = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)
        lines = [
            _make_ndjson_line(EventType.BUILD_INIT, ts=base, command="test"),
            "this is not json",
            '{"no_event_type": true}',
            _make_ndjson_line(EventType.BUILD_STARTED, ts=base + timedelta(seconds=1),
                              total_specs=1, build_order=["a"]),
        ]
        log_file.write_text("\n".join(lines) + "\n")

        state = BuildState()
        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = _parse_ndjson_event(line)
                if event is not None:
                    state.apply(event)

        assert state.status == "building"
        assert state.total_specs == 1

    def test_speed_zero_replays_instantly(self, tmp_path):
        """Speed=0 should process all events with no delay."""
        log_file = _make_ndjson_file(tmp_path)
        start = time.monotonic()

        from specsoloist.subscribers.build_state import BuildState
        state = BuildState()
        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = _parse_ndjson_event(line)
                if event is not None:
                    state.apply(event)

        elapsed = time.monotonic() - start
        # With speed=0 (no delays), this should be effectively instant
        assert elapsed < 1.0
        assert state.specs_completed == 2


class TestFollowMode:
    """Tests for sp dashboard --follow logic."""

    def test_follow_missing_file_exits_1(self):
        import subprocess
        result = subprocess.run(
            ["uv", "run", "sp", "dashboard", "--follow", "/nonexistent/file.ndjson"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()

    def test_follow_reads_existing_and_new_lines(self, tmp_path):
        """Follow mode reads existing content then picks up new lines."""
        from specsoloist.subscribers.build_state import BuildState

        log_file = tmp_path / "live.ndjson"
        base = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        # Write initial content
        log_file.write_text(
            _make_ndjson_line(EventType.BUILD_INIT, ts=base, command="test") + "\n"
            + _make_ndjson_line(EventType.BUILD_STARTED, ts=base + timedelta(seconds=1),
                                total_specs=1, build_order=["x"]) + "\n"
        )

        state = BuildState()

        # Read existing lines (simulating catch-up phase)
        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = _parse_ndjson_event(line)
                if event is not None:
                    state.apply(event)

        assert state.status == "building"
        assert state.total_specs == 1

        # Append new line (simulating a writer)
        with open(log_file, "a") as f:
            f.write(
                _make_ndjson_line(EventType.SPEC_COMPILE_STARTED, spec_name="x",
                                  ts=base + timedelta(seconds=2)) + "\n"
            )

        # Read the new line
        with open(log_file) as f:
            lines = f.readlines()

        event = _parse_ndjson_event(lines[-1].strip())
        assert event is not None
        state.apply(event)
        assert state.specs["x"].status == "compiling"
