"""Terminal dashboard for SpecSoloist builds.

Built on the Textual framework. Displays a live view of build progress:
navigable spec list with status icons, detail panel, and aggregate status bar.

File viewer (s/c/t/l keys): view spec source, generated code, generated tests,
or build log for the selected spec.
"""

from __future__ import annotations

import os
from typing import Callable, Optional

from rich.markup import escape as rich_escape
from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView, RichLog, Static

from .subscribers.build_state import BuildState, SpecState

# File type identifiers for the file viewer
VIEW_LOG = "log"
VIEW_SPEC = "spec"
VIEW_CODE = "code"
VIEW_TESTS = "tests"

# Callable that resolves (spec_name, file_type) -> file content or None
FileResolver = Callable[[str, str], Optional[str]]

# Map file extensions to Rich Syntax lexer names
_EXT_TO_LEXER: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
}


def _guess_lexer(path: str) -> str:
    """Guess the Rich Syntax lexer name from a file path."""
    _, ext = os.path.splitext(path)
    return _EXT_TO_LEXER.get(ext, "text")

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

    def set_file_content(self, content: str, file_path: str = "") -> None:
        """Display file content with syntax highlighting."""
        self.clear()
        lexer = _guess_lexer(file_path)
        syntax = Syntax(content, lexer, line_numbers=True, word_wrap=False)
        self.write(syntax)


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

    def update_spec(self, spec: SpecState | None, view_mode: str = VIEW_LOG,
                    file_content: str | None = None, file_path: str = "") -> None:
        """Update both info and log for a spec.

        Args:
            spec: The spec state to display.
            view_mode: One of VIEW_LOG, VIEW_SPEC, VIEW_CODE, VIEW_TESTS.
            file_content: Pre-resolved file content for file view modes.
            file_path: Path hint for syntax highlighting.
        """
        self.query_one("#spec-info", SpecInfoWidget).update_spec(spec)
        log_panel = self.query_one("#log-panel", LogPanel)

        if spec is None:
            log_panel.set_log([])
            return

        if view_mode == VIEW_LOG:
            log_panel.set_log(spec.log)
        elif file_content is not None:
            log_panel.set_file_content(file_content, file_path)
        else:
            log_panel.set_log([f"[dim]No {view_mode} file available[/dim]"])


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
        Binding("l", "view_log", "Log", show=True),
        Binding("s", "view_spec", "Spec", show=True),
        Binding("c", "view_code", "Code", show=True),
        Binding("t", "view_tests", "Tests", show=True),
    ]

    _build_state: reactive[BuildState | None] = reactive(None)
    _view_mode: reactive[str] = reactive(VIEW_LOG)

    def __init__(self, file_resolver: FileResolver | None = None, **kwargs) -> None:
        """Initialize the dashboard app.

        Args:
            file_resolver: Callback (spec_name, file_type) -> content or None.
            **kwargs: Passed to App.__init__.
        """
        super().__init__(**kwargs)
        self._file_resolver = file_resolver

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

    # -- View mode actions ---------------------------------------------------

    def action_view_log(self) -> None:
        """Switch to build log view."""
        self._view_mode = VIEW_LOG
        self._update_detail_for_selection()

    def action_view_spec(self) -> None:
        """Switch to spec source view."""
        self._view_mode = VIEW_SPEC
        self._update_detail_for_selection()

    def action_view_code(self) -> None:
        """Switch to generated code view."""
        self._view_mode = VIEW_CODE
        self._update_detail_for_selection()

    def action_view_tests(self) -> None:
        """Switch to generated tests view."""
        self._view_mode = VIEW_TESTS
        self._update_detail_for_selection()

    # -- Event handlers ------------------------------------------------------

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

                file_content = None
                file_path = ""
                if self._view_mode != VIEW_LOG and self._file_resolver is not None:
                    file_content = self._file_resolver(name, self._view_mode)
                    # Build a synthetic path for lexer detection
                    if file_content is not None:
                        if self._view_mode == VIEW_SPEC:
                            file_path = f"{name}.spec.md"
                        elif self._view_mode == VIEW_CODE:
                            file_path = f"{name}.py"
                        elif self._view_mode == VIEW_TESTS:
                            file_path = f"test_{name}.py"

                detail.update_spec(
                    spec, view_mode=self._view_mode,
                    file_content=file_content, file_path=file_path,
                )
                return

        detail.update_spec(None)
