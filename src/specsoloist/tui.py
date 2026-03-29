"""Terminal dashboard for SpecSoloist builds.

Built on the Textual framework. Displays a live view of build progress:
navigable spec list with status icons, detail panel, and aggregate status bar.
"""

from __future__ import annotations

from rich.markup import escape as rich_escape
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView, RichLog, Static

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


class SpecInfoWidget(Static):
    """Top portion of the detail panel — spec metadata."""

    DEFAULT_CSS = """
    SpecInfoWidget {
        height: auto;
        max-height: 8;
        padding: 0 1;
    }
    """

    def update_spec(self, spec: SpecState | None) -> None:
        """Update the info view for a spec."""
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
            lines.append(f"[red]Error: {rich_escape(spec.error)}[/red]")

        self.update("\n".join(lines))


class LogPanel(RichLog):
    """Scrollable log of events for the selected spec."""

    DEFAULT_CSS = """
    LogPanel {
        height: 1fr;
        border: solid $secondary;
        padding: 0 1;
    }
    """

    def set_log(self, lines: list[str]) -> None:
        """Replace log content with the given lines."""
        self.clear()
        for line in lines:
            self.write(line)


class SpecDetailWidget(Vertical):
    """Right panel — spec info + scrollable log."""

    DEFAULT_CSS = """
    SpecDetailWidget {
        width: 2fr;
        border: solid $secondary;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the spec info and log subwidgets."""
        yield SpecInfoWidget(id="spec-info")
        yield LogPanel(id="log-panel")

    def update_spec(self, spec: SpecState | None) -> None:
        """Update both info and log for a spec."""
        self.query_one("#spec-info", SpecInfoWidget).update_spec(spec)
        log_panel = self.query_one("#log-panel", LogPanel)
        if spec is not None:
            log_panel.set_log(spec.log)
        else:
            log_panel.set_log([])


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

        if state.status == "initializing":
            parts = []
            if state.command:
                parts.append(state.command)
            parts.append(state.phase or "Initializing...")
            self.update("  |  ".join(parts))
            return

        # Fatal error — show prominently with exit hint
        if state.status == "failed" and state.error:
            self.update(f"[bold red]Error: {rich_escape(state.error)}[/]  |  Press q to exit")
            return

        parts = [
            f"Tokens: {state.total_input_tokens:,} in / {state.total_output_tokens:,} out",
            f"Progress: {state.specs_completed}/{state.total_specs} specs",
        ]
        if state.elapsed > 0:
            parts.append(f"Elapsed: {state.elapsed:.1f}s")
        parts.append(f"Status: {state.status}")
        if state.status in ("completed", "failed"):
            parts.append("Press q to exit")

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
        self.query_one("#spec-info", SpecInfoWidget).update(
            "Waiting for build..."
        )

    def refresh_state(self, state: BuildState) -> None:
        """Update all widgets with new build state."""
        self._build_state = state

        spec_list = self.query_one("#spec-list", SpecListWidget)
        spec_list.update_specs(state.build_order, state.specs)

        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_state(state)

        # Show fatal error in the detail panel when no specs are available
        if state.error and not state.build_order:
            info = self.query_one("#spec-info", SpecInfoWidget)
            info.update(f"[bold red]{rich_escape(state.error)}[/]")
            return

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
