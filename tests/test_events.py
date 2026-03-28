"""Tests for the event bus and BuildEvent model."""

import threading
import time
from datetime import datetime, timezone

import pytest

from specsoloist.events import BuildEvent, EventBus, EventType


class TestBuildEvent:
    """Tests for the BuildEvent dataclass."""

    def test_create_with_defaults(self):
        e = BuildEvent(event_type=EventType.BUILD_STARTED)
        assert e.event_type == "build.started"
        assert e.spec_name is None
        assert e.data == {}
        assert isinstance(e.timestamp, datetime)

    def test_create_with_all_fields(self):
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
        e = BuildEvent(
            event_type=EventType.SPEC_COMPILE_COMPLETED,
            timestamp=ts,
            spec_name="config",
            data={"duration_seconds": 1.5},
        )
        assert e.event_type == "spec.compile.completed"
        assert e.timestamp == ts
        assert e.spec_name == "config"
        assert e.data["duration_seconds"] == 1.5

    def test_frozen(self):
        e = BuildEvent(event_type=EventType.BUILD_STARTED)
        with pytest.raises(AttributeError):
            e.event_type = "changed"

    def test_timestamp_is_utc(self):
        e = BuildEvent(event_type=EventType.BUILD_STARTED)
        assert e.timestamp.tzinfo is not None


class TestEventType:
    """Tests for event type constants."""

    def test_all_constants_are_strings(self):
        for attr in dir(EventType):
            if attr.isupper():
                assert isinstance(getattr(EventType, attr), str)

    def test_dotted_names(self):
        assert "." in EventType.BUILD_STARTED
        assert "." in EventType.SPEC_COMPILE_STARTED
        assert "." in EventType.LLM_REQUEST

    def test_expected_constants_exist(self):
        expected = [
            "BUILD_STARTED", "BUILD_COMPLETED", "BUILD_LEVEL_STARTED",
            "SPEC_COMPILE_STARTED", "SPEC_COMPILE_COMPLETED", "SPEC_COMPILE_FAILED",
            "SPEC_TESTS_STARTED", "SPEC_TESTS_COMPLETED",
            "SPEC_FIX_STARTED", "SPEC_FIX_COMPLETED",
            "LLM_REQUEST", "LLM_RESPONSE",
        ]
        for name in expected:
            assert hasattr(EventType, name), f"Missing EventType.{name}"


class TestEventBus:
    """Tests for the EventBus."""

    def test_subscribe_and_emit(self):
        received = []
        with EventBus() as bus:
            bus.subscribe(lambda e: received.append(e))
            bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))
        assert len(received) == 1
        assert received[0].event_type == "build.started"

    def test_multiple_subscribers(self):
        received_a = []
        received_b = []
        with EventBus() as bus:
            bus.subscribe(lambda e: received_a.append(e))
            bus.subscribe(lambda e: received_b.append(e))
            bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))
        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_events_received_in_order(self):
        received = []
        with EventBus() as bus:
            bus.subscribe(lambda e: received.append(e.event_type))
            bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))
            bus.emit(BuildEvent(event_type=EventType.SPEC_COMPILE_STARTED))
            bus.emit(BuildEvent(event_type=EventType.BUILD_COMPLETED))
        assert received == ["build.started", "spec.compile.started", "build.completed"]

    def test_thread_safety(self):
        received = []
        with EventBus() as bus:
            bus.subscribe(lambda e: received.append(e))

            threads = []
            for i in range(20):
                t = threading.Thread(
                    target=bus.emit,
                    args=(BuildEvent(
                        event_type=EventType.SPEC_COMPILE_STARTED,
                        spec_name=f"spec_{i}",
                    ),),
                )
                threads.append(t)
                t.start()
            for t in threads:
                t.join()

        assert len(received) == 20
        spec_names = {e.spec_name for e in received}
        assert spec_names == {f"spec_{i}" for i in range(20)}

    def test_context_manager_drains_events(self):
        received = []
        with EventBus() as bus:
            bus.subscribe(lambda e: received.append(e))
            for i in range(5):
                bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))
        # After __exit__, all events should be dispatched
        assert len(received) == 5

    def test_close_is_idempotent(self):
        bus = EventBus()
        bus.close()
        bus.close()  # Should not raise

    def test_emit_after_close_is_silent(self):
        received = []
        bus = EventBus()
        bus.subscribe(lambda e: received.append(e))
        bus.close()
        bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))
        # Give a moment for any accidental processing
        time.sleep(0.05)
        assert len(received) == 0

    def test_no_subscribers(self):
        """Emit without subscribers should not error."""
        with EventBus() as bus:
            bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))

    def test_subscribe_after_emit(self):
        """Late subscribers receive only subsequent events."""
        received = []
        with EventBus() as bus:
            bus.emit(BuildEvent(event_type=EventType.BUILD_STARTED))
            # Small delay to let the first event process
            time.sleep(0.05)
            bus.subscribe(lambda e: received.append(e))
            bus.emit(BuildEvent(event_type=EventType.BUILD_COMPLETED))
        assert len(received) == 1
        assert received[0].event_type == "build.completed"


class TestCoreEventBusIntegration:
    """Test that Core and Conductor accept event_bus parameter."""

    def test_core_accepts_event_bus(self, tmp_path):
        from specsoloist.core import SpecSoloistCore

        bus = EventBus()
        core = SpecSoloistCore(str(tmp_path), event_bus=bus)
        assert core._event_bus is bus
        bus.close()

    def test_core_default_no_bus(self, tmp_path):
        from specsoloist.core import SpecSoloistCore

        core = SpecSoloistCore(str(tmp_path))
        assert core._event_bus is None

    def test_core_emit_noop_without_bus(self, tmp_path):
        from specsoloist.core import SpecSoloistCore

        core = SpecSoloistCore(str(tmp_path))
        # Should not raise
        core._emit(EventType.BUILD_STARTED, total_specs=5)

    def test_core_emit_with_bus(self, tmp_path):
        from specsoloist.core import SpecSoloistCore

        received = []
        with EventBus() as bus:
            bus.subscribe(lambda e: received.append(e))
            core = SpecSoloistCore(str(tmp_path), event_bus=bus)
            core._emit(EventType.BUILD_STARTED, total_specs=5)
        assert len(received) == 1
        assert received[0].data["total_specs"] == 5

    def test_conductor_accepts_event_bus(self, tmp_path):
        from spechestra.conductor import SpecConductor

        bus = EventBus()
        conductor = SpecConductor(str(tmp_path), event_bus=bus)
        assert conductor._core._event_bus is bus
        bus.close()

    def test_conductor_default_no_bus(self, tmp_path):
        from spechestra.conductor import SpecConductor

        conductor = SpecConductor(str(tmp_path))
        assert conductor._core._event_bus is None
