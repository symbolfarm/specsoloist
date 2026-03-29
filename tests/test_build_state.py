"""Tests for BuildState model and TuiSubscriber."""

from unittest.mock import MagicMock

from specsoloist.events import BuildEvent, EventType
from specsoloist.subscribers.build_state import BuildState, SpecState
from specsoloist.subscribers.tui import TuiSubscriber


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _event(event_type: str, spec_name: str | None = None, **data) -> BuildEvent:
    """Create a BuildEvent with minimal boilerplate."""
    return BuildEvent(event_type=event_type, spec_name=spec_name, data=data)


def _started_state(specs: list[str] | None = None) -> BuildState:
    """Return a BuildState after BUILD_STARTED with the given spec names."""
    specs = specs or ["config", "parser", "runner"]
    state = BuildState()
    state.apply(_event(
        EventType.BUILD_STARTED,
        total_specs=len(specs),
        build_order=specs,
    ))
    return state


# ---------------------------------------------------------------------------
# BuildState.apply — BUILD events
# ---------------------------------------------------------------------------

class TestBuildEvents:
    def test_build_started_sets_status(self):
        state = BuildState()
        state.apply(_event(
            EventType.BUILD_STARTED,
            total_specs=3,
            build_order=["config", "parser", "runner"],
        ))
        assert state.status == "building"
        assert state.total_specs == 3
        assert state.build_order == ["config", "parser", "runner"]
        assert state.start_time is not None

    def test_build_started_creates_spec_states(self):
        state = _started_state(["config", "parser"])
        assert "config" in state.specs
        assert "parser" in state.specs
        assert state.specs["config"].status == "queued"

    def test_build_completed_with_no_failures(self):
        state = _started_state(["config"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        state.apply(_event(EventType.SPEC_COMPILE_COMPLETED, spec_name="config"))
        state.apply(_event(EventType.BUILD_COMPLETED))
        assert state.status == "completed"
        assert state.elapsed > 0

    def test_build_completed_with_failures(self):
        state = _started_state(["config"])
        state.apply(_event(
            EventType.SPEC_COMPILE_FAILED,
            spec_name="config",
            error="syntax error",
        ))
        state.apply(_event(EventType.BUILD_COMPLETED))
        assert state.status == "failed"

    def test_build_level_started_is_noop(self):
        state = _started_state()
        state.apply(_event(
            EventType.BUILD_LEVEL_STARTED,
            level=0,
            spec_names=["config"],
        ))
        # No state change — just informational
        assert state.status == "building"


# ---------------------------------------------------------------------------
# BuildState.apply — SPEC events
# ---------------------------------------------------------------------------

class TestSpecEvents:
    def test_compile_started(self):
        state = _started_state(["config"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        assert state.specs["config"].status == "compiling"

    def test_compile_completed(self):
        state = _started_state(["config"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        state.apply(_event(
            EventType.SPEC_COMPILE_COMPLETED,
            spec_name="config",
            duration_seconds=1.5,
        ))
        assert state.specs["config"].status == "passed"
        assert state.specs["config"].duration == 1.5
        assert state.specs_completed == 1

    def test_compile_failed(self):
        state = _started_state(["config"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        state.apply(_event(
            EventType.SPEC_COMPILE_FAILED,
            spec_name="config",
            error="LLM timeout",
        ))
        assert state.specs["config"].status == "failed"
        assert state.specs["config"].error == "LLM timeout"
        assert state.specs_failed == 1

    def test_tests_started(self):
        state = _started_state(["parser"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="parser"))
        state.apply(_event(EventType.SPEC_TESTS_STARTED, spec_name="parser"))
        assert state.specs["parser"].status == "testing"

    def test_tests_completed_success(self):
        state = _started_state(["parser"])
        state.apply(_event(EventType.SPEC_TESTS_STARTED, spec_name="parser"))
        state.apply(_event(
            EventType.SPEC_TESTS_COMPLETED,
            spec_name="parser",
            success=True,
        ))
        # Tests passing doesn't change status — spec.compile.completed does that
        assert state.specs["parser"].status == "testing"

    def test_tests_completed_failure(self):
        state = _started_state(["parser"])
        state.apply(_event(EventType.SPEC_TESTS_STARTED, spec_name="parser"))
        state.apply(_event(
            EventType.SPEC_TESTS_COMPLETED,
            spec_name="parser",
            success=False,
        ))
        assert state.specs["parser"].status == "failed"
        assert state.specs["parser"].error == "tests failed"
        assert state.specs_failed == 1


# ---------------------------------------------------------------------------
# Fix retry loop
# ---------------------------------------------------------------------------

class TestFixRetryLoop:
    def test_fix_started_increments_retries(self):
        state = _started_state(["parser"])
        state.apply(_event(
            EventType.SPEC_COMPILE_FAILED,
            spec_name="parser",
            error="bad output",
        ))
        state.apply(_event(EventType.SPEC_FIX_STARTED, spec_name="parser"))
        assert state.specs["parser"].status == "fixing"
        assert state.specs["parser"].retries == 1

    def test_fix_completed_sets_testing(self):
        state = _started_state(["parser"])
        state.apply(_event(EventType.SPEC_FIX_STARTED, spec_name="parser"))
        state.apply(_event(EventType.SPEC_FIX_COMPLETED, spec_name="parser"))
        assert state.specs["parser"].status == "testing"

    def test_multiple_fix_cycles(self):
        state = _started_state(["parser"])
        # First failure + fix
        state.apply(_event(
            EventType.SPEC_COMPILE_FAILED,
            spec_name="parser",
            error="error 1",
        ))
        state.apply(_event(EventType.SPEC_FIX_STARTED, spec_name="parser"))
        state.apply(_event(EventType.SPEC_FIX_COMPLETED, spec_name="parser"))
        # Second failure + fix
        state.apply(_event(EventType.SPEC_FIX_STARTED, spec_name="parser"))
        state.apply(_event(EventType.SPEC_FIX_COMPLETED, spec_name="parser"))

        assert state.specs["parser"].retries == 2
        assert state.specs["parser"].status == "testing"


# ---------------------------------------------------------------------------
# Parallel builds
# ---------------------------------------------------------------------------

class TestParallelBuilds:
    def test_multiple_specs_compiling_simultaneously(self):
        state = _started_state(["config", "resolver", "ui"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="resolver"))
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="ui"))

        assert state.specs["config"].status == "compiling"
        assert state.specs["resolver"].status == "compiling"
        assert state.specs["ui"].status == "compiling"

    def test_completed_count_increments_per_spec(self):
        state = _started_state(["config", "resolver"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="resolver"))
        state.apply(_event(EventType.SPEC_COMPILE_COMPLETED, spec_name="config"))
        assert state.specs_completed == 1
        state.apply(_event(EventType.SPEC_COMPILE_COMPLETED, spec_name="resolver"))
        assert state.specs_completed == 2


# ---------------------------------------------------------------------------
# LLM token tracking (build-level only)
# ---------------------------------------------------------------------------

class TestTokenTracking:
    def test_llm_response_accumulates_tokens(self):
        state = _started_state()
        state.apply(_event(
            EventType.LLM_RESPONSE,
            input_tokens=100,
            output_tokens=200,
        ))
        state.apply(_event(
            EventType.LLM_RESPONSE,
            input_tokens=150,
            output_tokens=300,
        ))
        assert state.total_input_tokens == 250
        assert state.total_output_tokens == 500

    def test_llm_response_handles_none_tokens(self):
        state = _started_state()
        state.apply(_event(
            EventType.LLM_RESPONSE,
            input_tokens=None,
            output_tokens=None,
        ))
        assert state.total_input_tokens == 0
        assert state.total_output_tokens == 0

    def test_llm_request_is_noop(self):
        state = _started_state()
        state.apply(_event(EventType.LLM_REQUEST, model="haiku"))
        # No state change
        assert state.total_input_tokens == 0


# ---------------------------------------------------------------------------
# Unknown events
# ---------------------------------------------------------------------------

class TestUnknownEvents:
    def test_unknown_event_type_is_ignored(self):
        state = _started_state()
        state.apply(_event("some.future.event", spec_name="config"))
        # No crash, no state change
        assert state.status == "building"

    def test_unknown_spec_name_creates_spec(self):
        state = BuildState()
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="new_spec"))
        assert "new_spec" in state.specs
        assert state.specs["new_spec"].status == "compiling"


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_to_dict_returns_plain_dict(self):
        state = _started_state(["config"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        d = state.to_dict()

        assert isinstance(d, dict)
        assert d["status"] == "building"
        assert d["total_specs"] == 1
        assert d["specs"]["config"]["status"] == "compiling"

    def test_to_dict_is_json_serializable(self):
        import json

        state = _started_state(["config", "parser"])
        state.apply(_event(
            EventType.LLM_RESPONSE,
            input_tokens=100,
            output_tokens=200,
        ))
        # Should not raise
        result = json.dumps(state.to_dict())
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Full event sequence
# ---------------------------------------------------------------------------

class TestSpecLog:
    def test_compile_started_logs(self):
        state = _started_state(["config"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        assert state.specs["config"].log == ["Generating implementation..."]

    def test_compile_completed_logs_with_duration(self):
        state = _started_state(["config"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        state.apply(_event(EventType.SPEC_COMPILE_COMPLETED, spec_name="config", duration_seconds=2.5))
        assert "2.5s" in state.specs["config"].log[-1]

    def test_test_failure_logs(self):
        state = _started_state(["p"])
        state.apply(_event(EventType.SPEC_TESTS_STARTED, spec_name="p"))
        state.apply(_event(EventType.SPEC_TESTS_COMPLETED, spec_name="p", success=False))
        assert "Tests failed" in state.specs["p"].log[-1]

    def test_fix_cycle_logs(self):
        state = _started_state(["x"])
        state.apply(_event(EventType.SPEC_FIX_STARTED, spec_name="x"))
        state.apply(_event(EventType.SPEC_FIX_COMPLETED, spec_name="x"))
        assert "Fix attempt 1" in state.specs["x"].log[0]
        assert "re-testing" in state.specs["x"].log[1]

    def test_full_sequence_log_accumulates(self):
        state = _started_state(["a"])
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="a"))
        state.apply(_event(EventType.SPEC_TESTS_STARTED, spec_name="a"))
        state.apply(_event(EventType.SPEC_TESTS_COMPLETED, spec_name="a", success=True))
        state.apply(_event(EventType.SPEC_COMPILE_COMPLETED, spec_name="a", duration_seconds=1.0))
        assert len(state.specs["a"].log) == 4


class TestFullSequence:
    def test_realistic_build_sequence(self):
        state = BuildState()

        # Build starts
        state.apply(_event(
            EventType.BUILD_STARTED,
            total_specs=2,
            build_order=["config", "parser"],
        ))
        assert state.status == "building"

        # Level 0: config compiles
        state.apply(_event(EventType.BUILD_LEVEL_STARTED, level=0, spec_names=["config"]))
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="config"))
        state.apply(_event(EventType.LLM_RESPONSE, input_tokens=500, output_tokens=1000))
        state.apply(_event(EventType.SPEC_TESTS_STARTED, spec_name="config"))
        state.apply(_event(EventType.SPEC_TESTS_COMPLETED, spec_name="config", success=True))
        state.apply(_event(EventType.SPEC_COMPILE_COMPLETED, spec_name="config", duration_seconds=3.2))

        assert state.specs["config"].status == "passed"
        assert state.specs_completed == 1

        # Level 1: parser compiles, fails, gets fixed
        state.apply(_event(EventType.BUILD_LEVEL_STARTED, level=1, spec_names=["parser"]))
        state.apply(_event(EventType.SPEC_COMPILE_STARTED, spec_name="parser"))
        state.apply(_event(EventType.LLM_RESPONSE, input_tokens=800, output_tokens=1500))
        state.apply(_event(EventType.SPEC_TESTS_STARTED, spec_name="parser"))
        state.apply(_event(EventType.SPEC_TESTS_COMPLETED, spec_name="parser", success=False))

        assert state.specs["parser"].status == "failed"

        # Fix cycle
        state.apply(_event(EventType.SPEC_FIX_STARTED, spec_name="parser"))
        state.apply(_event(EventType.LLM_RESPONSE, input_tokens=200, output_tokens=400))
        state.apply(_event(EventType.SPEC_FIX_COMPLETED, spec_name="parser"))
        state.apply(_event(EventType.SPEC_TESTS_STARTED, spec_name="parser"))
        state.apply(_event(EventType.SPEC_TESTS_COMPLETED, spec_name="parser", success=True))
        state.apply(_event(EventType.SPEC_COMPILE_COMPLETED, spec_name="parser", duration_seconds=8.1))

        # Build completes
        state.apply(_event(EventType.BUILD_COMPLETED))

        # Final assertions
        assert state.specs["parser"].status == "passed"
        assert state.specs["parser"].retries == 1
        assert state.specs_completed == 2
        assert state.total_input_tokens == 1500
        assert state.total_output_tokens == 2900
        assert state.elapsed > 0


# ---------------------------------------------------------------------------
# TuiSubscriber
# ---------------------------------------------------------------------------

class TestTuiSubscriber:
    def test_applies_event_to_state(self):
        sub = TuiSubscriber()
        sub(_event(
            EventType.BUILD_STARTED,
            total_specs=2,
            build_order=["config", "parser"],
        ))
        assert sub.state.status == "building"
        assert sub.state.total_specs == 2

    def test_calls_app_call_from_thread(self):
        app = MagicMock()
        sub = TuiSubscriber(app=app)
        sub(_event(
            EventType.BUILD_STARTED,
            total_specs=1,
            build_order=["config"],
        ))
        app.call_from_thread.assert_called_once_with(
            app.refresh_state, sub.state
        )

    def test_no_app_does_not_crash(self):
        sub = TuiSubscriber(app=None)
        # Should not raise
        sub(_event(EventType.BUILD_STARTED, total_specs=1, build_order=["x"]))
        assert sub.state.status == "building"

    def test_app_can_be_set_later(self):
        sub = TuiSubscriber()
        sub(_event(EventType.BUILD_STARTED, total_specs=1, build_order=["x"]))

        app = MagicMock()
        sub.app = app
        sub(_event(EventType.SPEC_COMPILE_STARTED, spec_name="x"))
        app.call_from_thread.assert_called_once()

    def test_integrates_with_event_bus(self):
        from specsoloist.events import EventBus

        sub = TuiSubscriber()
        with EventBus() as bus:
            bus.subscribe(sub)
            bus.emit(_event(
                EventType.BUILD_STARTED,
                total_specs=2,
                build_order=["a", "b"],
            ))
        # After bus closes (drains), state should reflect the event
        assert sub.state.status == "building"
        assert sub.state.total_specs == 2
