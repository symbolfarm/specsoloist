"""Terminal UI utilities for the SpecSoloist CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Shared console instance
console = Console()

# Module-level state
_quiet: bool = False
_json_mode: bool = False


def configure(quiet: bool = False, json_mode: bool = False) -> None:
    """Set module-level output flags."""
    global _quiet, _json_mode
    _quiet = quiet
    _json_mode = json_mode


def is_json_mode() -> bool:
    """Return true if JSON output mode is active."""
    return _json_mode


def is_quiet() -> bool:
    """Return true if quiet mode is active."""
    return _quiet


def print_header(title: str, subtitle: str | None = None) -> None:
    """Print a styled panel containing the title and optional subtitle."""
    if _quiet or _json_mode:
        return
    content = title
    if subtitle:
        content = f"{title}\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, style="bold blue"))


def print_success(message: str) -> None:
    """Print a success indicator followed by message."""
    if _quiet or _json_mode:
        return
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error prefix followed by message."""
    if _json_mode:
        return
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning prefix followed by message."""
    if _quiet or _json_mode:
        return
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info indicator followed by message."""
    if _quiet or _json_mode:
        return
    console.print(f"[blue]ℹ[/blue] {message}")


def print_step(message: str) -> None:
    """Print a step/arrow indicator followed by message."""
    if _quiet or _json_mode:
        return
    console.print(f"[cyan]→[/cyan] {message}")


def create_table(columns: list[str], title: str | None = None) -> Table:
    """Create and return a styled table with the given column headers."""
    table = Table(title=title, show_header=True, header_style="bold")
    for col in columns:
        table.add_column(col)
    return table


def spinner(message: str):
    """Return a context manager that displays a spinner with the given message."""
    return console.status(message)


def confirm(question: str) -> bool:
    """Prompt the user with question and [y/N], return True only if they enter y or Y."""
    response = input(f"{question} [y/N]: ").strip()
    return response.lower() == "y"
