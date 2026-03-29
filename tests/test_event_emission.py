"""Tests for event emission from core compilation pipeline."""

import os
from unittest.mock import patch

import pytest

from specsoloist.core import SpecSoloistCore
from specsoloist.events import EventBus, EventType


@pytest.fixture()
def project_dir(tmp_path):
    """Create a minimal project with a compilable spec."""
    src = tmp_path / "src"
    src.mkdir()

    spec = src / "greeter.spec.md"
    spec.write_text("""\
---
name: greeter
type: function
---

# Overview

A simple greeting function.

# Functions

## greet(name: str) -> str

Returns a greeting string like "Hello, {name}!".
""")
    return str(tmp_path)


def _collect_events(core, bus, fn):
    """Run fn(core), close bus, return received events."""
    received = []
    bus.subscribe(lambda e: received.append(e))
    fn(core)
    bus.close()  # drain queue so all events are dispatched
    return received


class TestCompileProjectEmission:
    """Test that compile_project emits the expected event sequence."""

    def test_build_started_and_completed(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        with patch.object(core, "compile_spec", return_value="Compiled"):
            events = _collect_events(core, bus, lambda c: c.compile_project(generate_tests=False))

        types = [e.event_type for e in events]
        assert types[0] == EventType.BUILD_SPECS_DISCOVERED
        assert types[1] == EventType.BUILD_DEPS_RESOLVED
        assert types[2] == EventType.BUILD_STARTED
        assert types[-1] == EventType.BUILD_COMPLETED

    def test_build_started_data(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        with patch.object(core, "compile_spec", return_value="Compiled"):
            events = _collect_events(core, bus, lambda c: c.compile_project(generate_tests=False))

        start = [e for e in events if e.event_type == EventType.BUILD_STARTED][0]
        assert start.data["total_specs"] == 1
        assert start.data["build_order"] == ["greeter"]
        assert "parallel" in start.data

    def test_build_completed_data(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        with patch.object(core, "compile_spec", return_value="Compiled"):
            events = _collect_events(core, bus, lambda c: c.compile_project(generate_tests=False))

        end = [e for e in events if e.event_type == EventType.BUILD_COMPLETED][0]
        assert end.data["specs_compiled"] == 1
        assert end.data["specs_failed"] == 0
        assert end.data["duration_seconds"] >= 0

    def test_spec_compile_started_and_completed(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        with patch.object(core, "compile_spec", return_value="Compiled"):
            events = _collect_events(core, bus, lambda c: c.compile_project(generate_tests=False))

        spec_types = [e.event_type for e in events if e.spec_name == "greeter"]
        assert EventType.SPEC_COMPILE_STARTED in spec_types
        assert EventType.SPEC_COMPILE_COMPLETED in spec_types

    def test_spec_compile_started_has_dependencies(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        with patch.object(core, "compile_spec", return_value="Compiled"):
            events = _collect_events(core, bus, lambda c: c.compile_project(generate_tests=False))

        start = [e for e in events if e.event_type == EventType.SPEC_COMPILE_STARTED][0]
        assert "dependencies" in start.data

    def test_spec_compile_completed_has_duration(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        with patch.object(core, "compile_spec", return_value="Compiled"):
            events = _collect_events(core, bus, lambda c: c.compile_project(generate_tests=False))

        completed = [e for e in events if e.event_type == EventType.SPEC_COMPILE_COMPLETED][0]
        assert completed.data["duration_seconds"] >= 0

    def test_spec_compile_failed(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        with patch.object(core, "compile_spec", side_effect=ValueError("LLM error")):
            events = _collect_events(core, bus, lambda c: c.compile_project(generate_tests=False))

        failed = [e for e in events if e.event_type == EventType.SPEC_COMPILE_FAILED]
        assert len(failed) == 1
        assert failed[0].spec_name == "greeter"
        assert "LLM error" in failed[0].data["error"]
        assert failed[0].data["error_type"] == "ValueError"

    def test_no_events_without_bus(self, project_dir):
        """Core without event bus should work normally."""
        core = SpecSoloistCore(project_dir)
        with patch.object(core, "compile_spec", return_value="Compiled"):
            result = core.compile_project(generate_tests=False)
        assert result.success

    def test_event_order(self, project_dir):
        """Events should follow: discovery → deps → build.started → spec events → build.completed."""
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        with patch.object(core, "compile_spec", return_value="Compiled"):
            events = _collect_events(core, bus, lambda c: c.compile_project(generate_tests=False))

        types = [e.event_type for e in events]
        assert types == [
            EventType.BUILD_SPECS_DISCOVERED,
            EventType.BUILD_DEPS_RESOLVED,
            EventType.BUILD_STARTED,
            EventType.SPEC_COMPILE_STARTED,
            EventType.SPEC_COMPILE_COMPLETED,
            EventType.BUILD_COMPLETED,
        ]


class TestParallelBuildEmission:
    """Test event emission during parallel builds."""

    def test_level_started_emitted(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        with patch.object(core, "compile_spec", return_value="Compiled"):
            events = _collect_events(
                core, bus,
                lambda c: c.compile_project(parallel=True, generate_tests=False),
            )

        level_events = [e for e in events if e.event_type == EventType.BUILD_LEVEL_STARTED]
        assert len(level_events) >= 1
        assert "spec_names" in level_events[0].data
        assert "level" in level_events[0].data


class TestRunTestsEmission:
    """Test event emission from run_tests."""

    def test_test_events_emitted(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        # Create a passing test file so runner can find it
        test_file = os.path.join(core.build_dir, "test_greeter.py")
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, "w") as f:
            f.write("def test_pass(): assert True\n")

        events = _collect_events(core, bus, lambda c: c.run_tests("greeter"))

        types = [e.event_type for e in events]
        assert EventType.SPEC_TESTS_STARTED in types
        assert EventType.SPEC_TESTS_COMPLETED in types

    def test_test_completed_has_fields(self, project_dir):
        bus = EventBus()
        core = SpecSoloistCore(project_dir, event_bus=bus)

        test_file = os.path.join(core.build_dir, "test_greeter.py")
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, "w") as f:
            f.write("def test_pass(): assert True\n")

        events = _collect_events(core, bus, lambda c: c.run_tests("greeter"))

        completed = [e for e in events if e.event_type == EventType.SPEC_TESTS_COMPLETED][0]
        assert "success" in completed.data
        assert "duration_seconds" in completed.data
        assert "return_code" in completed.data
