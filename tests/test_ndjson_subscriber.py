"""Tests for the NDJSON event subscriber."""

import json
from io import StringIO

import pytest

from specsoloist.events import BuildEvent, EventBus, EventType
from specsoloist.subscribers.ndjson import NdjsonSubscriber


class TestNdjsonSubscriber:
    """Tests for NdjsonSubscriber."""

    def test_writes_valid_json_lines(self):
        buf = StringIO()
        sub = NdjsonSubscriber(buf)

        with EventBus() as bus:
            bus.subscribe(sub)
            bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED, data={"total_specs": 5}))
            bus.emit(BuildEvent(event_type=EventType.BUILD_COMPLETED, data={"duration_seconds": 1.5}))

        lines = buf.getvalue().strip().split("\n")
        assert len(lines) == 2

        for line in lines:
            parsed = json.loads(line)
            assert "event_type" in parsed
            assert "timestamp" in parsed

    def test_event_type_preserved(self):
        buf = StringIO()
        sub = NdjsonSubscriber(buf)

        with EventBus() as bus:
            bus.subscribe(sub)
            bus.emit(BuildEvent(event_type=EventType.SPEC_COMPILE_STARTED, spec_name="config"))

        record = json.loads(buf.getvalue().strip())
        assert record["event_type"] == "spec.compile.started"
        assert record["spec_name"] == "config"

    def test_data_fields_included(self):
        buf = StringIO()
        sub = NdjsonSubscriber(buf)

        with EventBus() as bus:
            bus.subscribe(sub)
            bus.emit(BuildEvent(
                event_type=EventType.SPEC_COMPILE_COMPLETED,
                spec_name="parser",
                data={"duration_seconds": 2.5, "output_path": "build/parser.py"},
            ))

        record = json.loads(buf.getvalue().strip())
        assert record["duration_seconds"] == 2.5
        assert record["output_path"] == "build/parser.py"

    def test_timestamp_is_iso8601(self):
        buf = StringIO()
        sub = NdjsonSubscriber(buf)

        with EventBus() as bus:
            bus.subscribe(sub)
            bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))

        record = json.loads(buf.getvalue().strip())
        ts = record["timestamp"]
        # ISO 8601 timestamps contain T and +/timezone info
        assert "T" in ts

    def test_spec_name_none_included(self):
        buf = StringIO()
        sub = NdjsonSubscriber(buf)

        with EventBus() as bus:
            bus.subscribe(sub)
            bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))

        record = json.loads(buf.getvalue().strip())
        assert record["spec_name"] is None

    def test_multiple_events_one_per_line(self):
        buf = StringIO()
        sub = NdjsonSubscriber(buf)

        with EventBus() as bus:
            bus.subscribe(sub)
            for i in range(5):
                bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))

        lines = buf.getvalue().strip().split("\n")
        assert len(lines) == 5
        for line in lines:
            json.loads(line)  # each line is valid JSON

    def test_flushes_after_each_event(self):
        """Subscriber should flush after each write for real-time visibility."""
        buf = StringIO()
        sub = NdjsonSubscriber(buf)

        # Call directly (not through bus) to test synchronously
        sub(BuildEvent(event_type=EventType.BUILD_STARTED))
        assert buf.getvalue().strip() != ""
