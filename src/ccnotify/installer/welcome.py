"""Welcome screen and ASCII art display for CCNotify installer."""

import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.align import Align

console = Console()

CCNOTIFY_ASCII_ART = """
 ██████╗ ██████╗███╗   ██╗ ██████╗ ████████╗██╗███████╗██╗   ██╗
██╔════╝██╔════╝████╗  ██║██╔═══██╗╚══██╔══╝██║██╔════╝╚██╗ ██╔╝
██║     ██║     ██╔██╗ ██║██║   ██║   ██║   ██║█████╗   ╚████╔╝ 
██║     ██║     ██║╚██╗██║██║   ██║   ██║   ██║██╔══╝    ╚██╔╝  
╚██████╗╚██████╗██║ ╚████║╚██████╔╝   ██║   ██║██║        ██║   
 ╚═════╝ ╚═════╝╚═╝  ╚═══╝ ╚═════╝    ╚═╝   ╚═╝╚═╝        ╚═╝   
"""


def display_welcome_screen(version: str, platform: str, is_update: bool = False) -> None:
    """Display the animated welcome screen with ANSI art."""
    console.clear()

    # Create gradient ASCII art
    ascii_text = Text(CCNOTIFY_ASCII_ART)
    ascii_text.stylize("bold blue", 0, len(CCNOTIFY_ASCII_ART) // 3)
    ascii_text.stylize(
        "bold cyan", len(CCNOTIFY_ASCII_ART) // 3, (len(CCNOTIFY_ASCII_ART) * 2) // 3
    )
    ascii_text.stylize("bold magenta", (len(CCNOTIFY_ASCII_ART) * 2) // 3, len(CCNOTIFY_ASCII_ART))

    # Create subtitle
    subtitle = "Voice Notification System for Claude Code"
    subtitle_text = Text(subtitle, style="italic dim")

    # Create version and platform info
    action = "UPDATE" if is_update else "INSTALLATION"
    info_text = Text(f"v{version} • {platform} • {action}", style="dim")

    # Create a Group to combine elements properly
    from rich.console import Group

    content = Group(
        Align.center(ascii_text),
        "",  # Empty line
        Align.center(subtitle_text),
        "",  # Empty line
        Align.center(info_text),
    )

    # Create panel with border
    panel = Panel(
        content,
        border_style="blue",
        padding=(1, 2),
        title=(
            "[bold blue]CCNotify Installer[/bold blue]"
            if not is_update
            else "[bold blue]CCNotify Updater[/bold blue]"
        ),
        title_align="center",
    )

    console.print(panel)
    console.print()


def display_progress_header(step: str, current: int, total: int) -> None:
    """Display a progress header for installation steps."""
    progress_text = f"[bold cyan]Step {current}/{total}:[/bold cyan] {step}"
    console.print(progress_text)
    console.print()


def display_success_message(message: str) -> None:
    """Display a success message with styling."""
    success_panel = Panel(
        Text(message, style="bold green", justify="center"),
        border_style="green",
        title="[bold green]✓ Success[/bold green]",
        title_align="center",
    )
    console.print(success_panel)


def display_error_message(message: str, details: str = None) -> None:
    """Display an error message with optional details."""
    error_text = Text(message, style="bold red")
    if details:
        error_text.append(f"\n\n{details}", style="dim red")

    error_panel = Panel(
        error_text, border_style="red", title="[bold red]✗ Error[/bold red]", title_align="center"
    )
    console.print(error_panel)


def display_warning_message(message: str) -> None:
    """Display a warning message."""
    warning_panel = Panel(
        Text(message, style="bold yellow", justify="center"),
        border_style="yellow",
        title="[bold yellow]⚠ Warning[/bold yellow]",
        title_align="center",
    )
    console.print(warning_panel)


def animate_thinking(message: str = "Processing", duration: float = 2.0) -> None:
    """Display an animated thinking indicator."""
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    end_time = time.time() + duration

    with console.status(f"[bold blue]{message}...", spinner="dots"):
        while time.time() < end_time:
            time.sleep(0.1)


if __name__ == "__main__":
    # Demo the welcome screen
    display_welcome_screen("1.0.0", "macOS", False)
    time.sleep(2)
    display_welcome_screen("1.0.0", "macOS", True)
