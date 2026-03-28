"""TuiSubscriber — thin bridge from EventBus to a Textual app.

Holds a BuildState and a reference to the Textual app. On each event,
applies it to the state and notifies the app via call_from_thread().

No Textual import at module level — the app reference uses a Protocol
so this module stays testable without Textual installed.
"""

from __future__ import annotations

from typing import Any, Protocol

from ..events import BuildEvent
from .build_state import BuildState


class TuiApp(Protocol):
    """Protocol for the Textual app interface used by TuiSubscriber."""

    def call_from_thread(self, callback: Any, *args: Any) -> None:
        """Schedule a callback on the UI thread."""
        ...

    def refresh_state(self, state: BuildState) -> None:
        """Update the display with new build state."""
        ...


class TuiSubscriber:
    """Event bus subscriber that maintains BuildState and notifies a TUI app."""

    def __init__(self, app: TuiApp | None = None) -> None:
        """Initialize with an optional Textual app reference.

        Args:
            app: Textual app to notify on state changes. Can be set later
                via the app property, or left None for headless use.
        """
        self.state = BuildState()
        self._app = app

    @property
    def app(self) -> TuiApp | None:
        """The Textual app receiving state updates."""
        return self._app

    @app.setter
    def app(self, value: TuiApp | None) -> None:
        self._app = value

    def __call__(self, event: BuildEvent) -> None:
        """Apply event to state and notify the app."""
        self.state.apply(event)
        if self._app is not None:
            self._app.call_from_thread(self._app.refresh_state, self.state)
