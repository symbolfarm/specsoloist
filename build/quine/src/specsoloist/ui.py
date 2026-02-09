"""
UI module for SpecSoloist CLI using Rich.

Provides styled output functions for headers, status messages, tables,
spinners, and user confirmation prompts. All output goes through a shared
console instance.
"""

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

console = Console(theme=theme)


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """
    Print a styled panel containing the title and optional subtitle.

    Args:
        title: Main title text
        subtitle: Optional subtitle text
    """
    console.print()
    content = Text(subtitle, justify="center", style="dim") if subtitle else ""
    console.print(Panel(
        content,
        title=f"[bold blue]{title}[/]",
        border_style="blue",
        expand=False
    ))
    console.print()


def print_success(message: str) -> None:
    """
    Print a success indicator followed by message.

    Args:
        message: Success message to display
    """
    console.print(f"[success]✔[/] {message}")


def print_error(message: str) -> None:
    """
    Print an error prefix followed by message.

    Args:
        message: Error message to display
    """
    console.print(f"[error]✖ Error:[/] {message}")


def print_warning(message: str) -> None:
    """
    Print a warning prefix followed by message.

    Args:
        message: Warning message to display
    """
    console.print(f"[warning]! Warning:[/] {message}")


def print_info(message: str) -> None:
    """
    Print an info indicator followed by message.

    Args:
        message: Info message to display
    """
    console.print(f"[info]ℹ[/] {message}")


def print_step(message: str) -> None:
    """
    Print a step/arrow indicator followed by message.

    Args:
        message: Step message to display
    """
    console.print(f"[bold blue]→[/] {message}")


def create_table(columns: List[str], title: Optional[str] = None) -> Table:
    """
    Create and return a styled table with the given column headers.

    Args:
        columns: List of column header names
        title: Optional table title

    Returns:
        Table object ready for add_row() calls
    """
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        border_style="dim"
    )
    for col in columns:
        table.add_column(col)
    return table


def spinner(message: str) -> Status:
    """
    Return a context manager that displays a spinner with the given message.

    Args:
        message: Status message to display

    Returns:
        Context manager that shows a spinner while active
    """
    return console.status(f"[bold blue]{message}[/]", spinner="dots")


def confirm(question: str) -> bool:
    """
    Prompt the user with question and [y/N], return True only if they enter y or Y.

    Args:
        question: Yes/no question to ask

    Returns:
        True only if user enters 'y' or 'Y', False otherwise
    """
    response = console.input(f"[bold yellow]{question} [y/N]: [/]")
    return response.lower() == 'y'
