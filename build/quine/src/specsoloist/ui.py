"""UI module for SpecSoloist CLI using Rich."""

import os
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.status import Status

# Custom theme for SpecSoloist
theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "highlight": "bold magenta",
    "dim": "dim",
})

console = Console(theme=theme, no_color="NO_COLOR" in os.environ)

# Module-level flags for output mode
_quiet: bool = False
_json_mode: bool = False


def configure(quiet: bool = False, json_mode: bool = False) -> None:
    """Configure the UI output mode.

    Call this once at startup (e.g. after parsing --quiet / --json flags).

    - quiet=True: suppress all non-error output (Rich console set to quiet=True)
    - json_mode=True: disable Rich output entirely; commands emit plain JSON
    """
    global console, _quiet, _json_mode
    _quiet = quiet
    _json_mode = json_mode
    no_color = "NO_COLOR" in os.environ or json_mode
    # In JSON or quiet mode, suppress Rich decorations
    console = Console(
        theme=theme,
        no_color=no_color,
        quiet=quiet or json_mode,
    )


def is_json_mode() -> bool:
    """Return True if JSON output mode is active."""
    return _json_mode


def is_quiet() -> bool:
    """Return True if quiet mode is active."""
    return _quiet


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a styled header."""
    console.print()
    console.print(Panel(
        Text(subtitle, justify="center", style="dim") if subtitle else "",
        title=f"[bold blue]{title}[/]",
        border_style="blue",
        expand=False
    ))
    console.print()


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[success]✔[/] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[error]✖ Error:[/] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[warning]! Warning:[/] {message}")


def print_info(message: str) -> None:
    """Print an informational message."""
    console.print(f"[info]ℹ[/] {message}")


def print_step(message: str) -> None:
    """Print a step in a process."""
    console.print(f"[bold blue]→[/] {message}")


def create_table(columns: List[str], title: Optional[str] = None) -> Table:
    """Create a styled table."""
    table = Table(title=title, show_header=True, header_style="bold cyan", border_style="dim")
    for col in columns:
        table.add_column(col)
    return table


def spinner(message: str) -> Status:
    """Return a status spinner context manager."""
    return console.status(f"[bold blue]{message}[/]", spinner="dots")


def confirm(question: str) -> bool:
    """Ask for user confirmation (simple wrapper, rich prompt could be used too)."""
    response = console.input(f"[bold yellow]{question} [y/N]: [/]")
    return response.lower() == 'y'
