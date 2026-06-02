from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

console = Console()


def print_welcome():
    panel = Panel.fit(
        "[bold cyan]Coding Agent[/bold cyan]\n"
        "\n"
        "Coordinates specialized sub-agents to help complete tasks faster.\n"
        "[dim]Type your coding request below. Use /help for commands.[/dim]",
        title="Welcome",
        border_style="cyan",
        box=box.ROUNDED,
    )
    console.print(panel)


def print_user_message(text: str):
    console.print(f"\n[bold yellow]You[/bold yellow]")
    console.print(f"[yellow]{text}[/yellow]")


def print_assistant_message(text: str):
    console.print(f"\n[bold green]Agent[/bold green]")
    md = Markdown(text)
    console.print(Panel(md, border_style="green", box=box.ROUNDED))


def print_error(text: str):
    console.print(f"[bold red]Error:[/bold red] {text}")


def print_subtask_progress(subtasks: list) -> Progress:
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    )
    progress.start()
    return progress


def get_user_input() -> str:
    try:
        text = console.input("[bold yellow]You >[/bold yellow] ").strip()
        return text
    except (EOFError, KeyboardInterrupt):
        return ""
