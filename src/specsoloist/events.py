"""Event bus for SpecSoloist build observability.

Components emit BuildEvents during compilation; subscribers handle them
for logging, TUI display, or network streaming. Thread-safe via queue.Queue.
"""

import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional


class EventType:
    """String constants for event types."""

    BUILD_STARTED = "build.started"
    BUILD_COMPLETED = "build.completed"
    BUILD_LEVEL_STARTED = "build.level.started"
    SPEC_COMPILE_STARTED = "spec.compile.started"
    SPEC_COMPILE_COMPLETED = "spec.compile.completed"
    SPEC_COMPILE_FAILED = "spec.compile.failed"
    SPEC_TESTS_STARTED = "spec.tests.started"
    SPEC_TESTS_COMPLETED = "spec.tests.completed"
    SPEC_FIX_STARTED = "spec.fix.started"
    SPEC_FIX_COMPLETED = "spec.fix.completed"
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"


@dataclass(frozen=True)
class BuildEvent:
    """A single observable event during a build."""

    event_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    spec_name: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


# Sentinel object to signal the consumer thread to stop
_STOP = object()


class EventBus:
    """Publish-subscribe event bus for build observability.

    Thread-safe: emit() can be called from any thread. Subscribers are
    called sequentially on a dedicated consumer thread.
    """

    def __init__(self) -> None:
        """Create an event bus with a background consumer thread."""
        self._queue: queue.Queue = queue.Queue()
        self._subscribers: list[Callable[[BuildEvent], None]] = []
        self._closed = False
        self._lock = threading.Lock()
        self._consumer = threading.Thread(
            target=self._consume, daemon=True, name="event-bus-consumer"
        )
        self._consumer.start()

    def subscribe(self, handler: Callable[[BuildEvent], None]) -> None:
        """Register a subscriber. Called in registration order."""
        with self._lock:
            self._subscribers.append(handler)

    def emit(self, event: BuildEvent) -> None:
        """Publish an event. Thread-safe, non-blocking."""
        if self._closed:
            return
        self._queue.put(event)

    def close(self) -> None:
        """Drain remaining events and stop the consumer thread."""
        if self._closed:
            return
        self._closed = True
        self._queue.put(_STOP)
        self._consumer.join()

    def _consume(self) -> None:
        """Consumer loop: dispatch events to subscribers."""
        while True:
            item = self._queue.get()
            if item is _STOP:
                break
            with self._lock:
                subscribers = list(self._subscribers)
            for handler in subscribers:
                handler(item)

    def __enter__(self) -> "EventBus":
        """Enter context manager."""
        return self

    def __exit__(self, *exc: object) -> None:
        """Exit context manager, draining and closing the bus."""
        self.close()
