"""
UI module for Specular CLI using Rich.
"""

from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.status import Status

# Custom theme for Specular
theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "highlight": "bold magenta",
    "dim": "dim",
})

console = Console(theme=theme)

def print_header(title: str, subtitle: str = ""):
    """Print a styled header."""
    console.print()
    console.print(Panel(
        Text(subtitle, justify="center", style="dim") if subtitle else "",
        title=f"[bold blue]{title}[/]",
        border_style="blue",
        expand=False
    ))
    console.print()

def print_success(message: str):
    """Print a success message."""
    console.print(f"[success]✔[/] {message}")

def print_error(message: str):
    """Print an error message."""
    console.print(f"[error]✖ Error:[/] {message}")

def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[warning]! Warning:[/] {message}")

def print_info(message: str):
    """Print an informational message."""
    console.print(f"[info]ℹ[/] {message}")

def print_step(message: str):
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
