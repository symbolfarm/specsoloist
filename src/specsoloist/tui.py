"""Terminal dashboard for SpecSoloist builds.

Built on the Textual framework. Displays a live view of build progress:
navigable spec list with status icons, detail panel, and aggregate status bar.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView, Static

from .subscribers.build_state import BuildState, SpecState

# ---------------------------------------------------------------------------
# Status icon mapping
# ---------------------------------------------------------------------------

_STATUS_ICONS: dict[str, str] = {
    "queued": "◌",
    "compiling": "●",
    "testing": "●",
    "fixing": "●",
    "passed": "○",
    "failed": "✖",
}


def _status_icon(status: str) -> str:
    return _STATUS_ICONS.get(status, "?")


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------


class SpecListWidget(ListView):
    """Left panel — navigable list of specs with status icons."""

    DEFAULT_CSS = """
    SpecListWidget {
        width: 1fr;
        min-width: 24;
        border: solid $secondary;
    }
    SpecListWidget > ListItem {
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        """Initialize with an empty spec list."""
        super().__init__(**kwargs)
        self._spec_names: list[str] = []

    @property
    def spec_names(self) -> list[str]:
        """Spec names currently displayed, in order."""
        return list(self._spec_names)

    def update_specs(self, build_order: list[str], specs: dict[str, SpecState]) -> None:
        """Re-render the spec list, preserving selection."""
        # Remember current selection
        selected_index = self.index

        self.clear()
        self._spec_names = list(build_order)

        for name in build_order:
            spec = specs.get(name)
            status = spec.status if spec else "queued"
            icon = _status_icon(status)
            item = ListItem(Label(f"{icon} {name}"), name=name)
            self.append(item)

        # Restore selection
        if selected_index is not None and 0 <= selected_index < len(build_order):
            self.index = selected_index
        elif build_order:
            self.index = 0


class SpecDetailWidget(Static):
    """Right panel — details for the currently selected spec."""

    DEFAULT_CSS = """
    SpecDetailWidget {
        width: 2fr;
        border: solid $secondary;
        padding: 1 2;
    }
    """

    def update_spec(self, spec: SpecState | None) -> None:
        """Update the detail view for a spec."""
        if spec is None:
            self.update("Select a spec to view details")
            return

        lines = [
            f"[bold]{spec.name}[/bold]",
            f"Status: {_status_icon(spec.status)} {spec.status}",
        ]
        if spec.duration is not None:
            lines.append(f"Duration: {spec.duration:.1f}s")
        if spec.retries > 0:
            lines.append(f"Retries: {spec.retries}")
        if spec.input_tokens or spec.output_tokens:
            lines.append(f"Tokens: {spec.input_tokens:,} in / {spec.output_tokens:,} out")
        if spec.error:
            lines.append(f"[red]Error: {spec.error}[/red]")

        self.update("\n".join(lines))


class StatusBar(Static):
    """Bottom bar — aggregate build statistics."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        """Initialize with idle message."""
        super().__init__("No build in progress", **kwargs)

    def update_state(self, state: BuildState) -> None:
        """Update the status bar with aggregate build state."""
        if state.status == "idle":
            self.update("No build in progress")
            return

        parts = [
            f"Tokens: {state.total_input_tokens:,} in / {state.total_output_tokens:,} out",
            f"Progress: {state.specs_completed}/{state.total_specs} specs",
        ]
        if state.elapsed > 0:
            parts.append(f"Elapsed: {state.elapsed:.1f}s")
        parts.append(f"Status: {state.status}")

        self.update("  |  ".join(parts))


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------


class DashboardApp(App):
    """SpecSoloist build dashboard."""

    TITLE = "SpecSoloist Dashboard"

    CSS = """
    #main {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    _build_state: reactive[BuildState | None] = reactive(None)

    def compose(self) -> ComposeResult:
        """Create the initial layout."""
        yield StatusBar(id="status-bar")
        with Horizontal(id="main"):
            yield SpecListWidget(id="spec-list")
            yield SpecDetailWidget(id="spec-detail")

    def on_mount(self) -> None:
        """Show waiting message on startup."""
        self.query_one("#spec-detail", SpecDetailWidget).update(
            "Waiting for build..."
        )

    def refresh_state(self, state: BuildState) -> None:
        """Update all widgets with new build state."""
        self._build_state = state

        spec_list = self.query_one("#spec-list", SpecListWidget)
        spec_list.update_specs(state.build_order, state.specs)

        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_state(state)

        # Update detail panel for currently selected spec
        self._update_detail_for_selection()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle spec selection from the list."""
        self._update_detail_for_selection()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update detail panel when highlight changes."""
        self._update_detail_for_selection()

    def _update_detail_for_selection(self) -> None:
        """Sync the detail panel with the current list selection."""
        state = self._build_state
        if state is None:
            return

        spec_list = self.query_one("#spec-list", SpecListWidget)
        detail = self.query_one("#spec-detail", SpecDetailWidget)

        if spec_list.index is not None and spec_list.spec_names:
            idx = spec_list.index
            if 0 <= idx < len(spec_list.spec_names):
                name = spec_list.spec_names[idx]
                spec = state.specs.get(name)
                detail.update_spec(spec)
                return

        detail.update_spec(None)
