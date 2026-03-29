"""BuildState model for accumulating build events into displayable state.

Pure data layer with no UI dependencies. BuildState absorbs BuildEvents via
apply() and maintains the current snapshot of a build — usable by TUI, SSE,
and NDJSON replay consumers.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

from ..events import BuildEvent, EventType


@dataclass
class SpecState:
    """Per-spec compilation state."""

    name: str
    status: str = "queued"  # queued | compiling | testing | passed | failed | fixing
    duration: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None
    retries: int = 0
    log: list[str] = field(default_factory=list)


@dataclass
class BuildState:
    """Mutable model that absorbs BuildEvents and maintains current state.

    This is the single source of truth for all display layers (TUI, SSE
    /status, NDJSON replay). Fully reconstructable from its fields — no
    event history required.
    """

    specs: dict[str, SpecState] = field(default_factory=dict)
    build_order: list[str] = field(default_factory=list)
    total_specs: int = 0
    specs_completed: int = 0
    specs_failed: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    start_time: float | None = None
    elapsed: float = 0.0
    status: str = "idle"  # idle | building | completed | failed

    def apply(self, event: BuildEvent) -> None:
        """Apply a single event to update state. Ignores unknown event types."""
        handler = _EVENT_HANDLERS.get(event.event_type)
        if handler is not None:
            handler(self, event)

    def to_dict(self) -> dict:
        """Serialize to a plain dict suitable for JSON encoding."""
        d = asdict(self)
        # asdict converts SpecState values to dicts already
        return d


# ---------------------------------------------------------------------------
# Event handlers — one per event type
# ---------------------------------------------------------------------------

def _on_build_started(state: BuildState, event: BuildEvent) -> None:
    state.status = "building"
    state.start_time = time.monotonic()
    state.total_specs = event.data.get("total_specs", 0)
    build_order = event.data.get("build_order", [])
    state.build_order = list(build_order)
    for name in build_order:
        if name not in state.specs:
            state.specs[name] = SpecState(name=name)


def _on_build_completed(state: BuildState, event: BuildEvent) -> None:
    if state.start_time is not None:
        state.elapsed = time.monotonic() - state.start_time
    state.status = "failed" if state.specs_failed > 0 else "completed"


def _on_build_level_started(state: BuildState, event: BuildEvent) -> None:
    # Informational — no state change needed beyond what spec events provide
    pass


def _on_spec_compile_started(state: BuildState, event: BuildEvent) -> None:
    spec = _ensure_spec(state, event.spec_name)
    spec.status = "compiling"
    spec.log.append("Generating implementation...")


def _on_spec_compile_completed(state: BuildState, event: BuildEvent) -> None:
    spec = _ensure_spec(state, event.spec_name)
    spec.status = "passed"
    spec.duration = event.data.get("duration_seconds")
    state.specs_completed += 1
    duration_str = f" ({spec.duration:.1f}s)" if spec.duration else ""
    spec.log.append(f"Compilation complete{duration_str}")


def _on_spec_compile_failed(state: BuildState, event: BuildEvent) -> None:
    spec = _ensure_spec(state, event.spec_name)
    spec.status = "failed"
    spec.error = event.data.get("error")
    state.specs_failed += 1
    spec.log.append(f"Compilation failed: {spec.error or 'unknown error'}")


def _on_spec_tests_started(state: BuildState, event: BuildEvent) -> None:
    spec = _ensure_spec(state, event.spec_name)
    spec.status = "testing"
    spec.log.append("Running tests...")


def _on_spec_tests_completed(state: BuildState, event: BuildEvent) -> None:
    spec = _ensure_spec(state, event.spec_name)
    success = event.data.get("success", False)
    if not success:
        spec.status = "failed"
        # Only increment specs_failed if this is the first failure
        # (not already counted from a compile failure)
        if spec.error is None:
            state.specs_failed += 1
        spec.error = "tests failed"
        spec.log.append("Tests failed")
    else:
        spec.log.append("Tests passed")


def _on_spec_fix_started(state: BuildState, event: BuildEvent) -> None:
    spec = _ensure_spec(state, event.spec_name)
    spec.status = "fixing"
    spec.retries += 1
    spec.log.append(f"Fix attempt {spec.retries}...")


def _on_spec_fix_completed(state: BuildState, event: BuildEvent) -> None:
    spec = _ensure_spec(state, event.spec_name)
    # After a fix, the spec goes back to testing (tests will be re-run)
    spec.status = "testing"
    spec.log.append("Fix applied, re-testing...")


def _on_llm_response(state: BuildState, event: BuildEvent) -> None:
    input_tokens = event.data.get("input_tokens") or 0
    output_tokens = event.data.get("output_tokens") or 0
    state.total_input_tokens += input_tokens
    state.total_output_tokens += output_tokens


def _on_llm_request(state: BuildState, event: BuildEvent) -> None:
    # Informational — tracked for completeness, no state change
    pass


# ---------------------------------------------------------------------------
# Handler dispatch table
# ---------------------------------------------------------------------------

_EVENT_HANDLERS: dict[str, callable] = {
    EventType.BUILD_STARTED: _on_build_started,
    EventType.BUILD_COMPLETED: _on_build_completed,
    EventType.BUILD_LEVEL_STARTED: _on_build_level_started,
    EventType.SPEC_COMPILE_STARTED: _on_spec_compile_started,
    EventType.SPEC_COMPILE_COMPLETED: _on_spec_compile_completed,
    EventType.SPEC_COMPILE_FAILED: _on_spec_compile_failed,
    EventType.SPEC_TESTS_STARTED: _on_spec_tests_started,
    EventType.SPEC_TESTS_COMPLETED: _on_spec_tests_completed,
    EventType.SPEC_FIX_STARTED: _on_spec_fix_started,
    EventType.SPEC_FIX_COMPLETED: _on_spec_fix_completed,
    EventType.LLM_REQUEST: _on_llm_request,
    EventType.LLM_RESPONSE: _on_llm_response,
}


def _ensure_spec(state: BuildState, name: str | None) -> SpecState:
    """Get or create a SpecState by name."""
    if name is None:
        name = "__unknown__"
    if name not in state.specs:
        state.specs[name] = SpecState(name=name)
    return state.specs[name]
