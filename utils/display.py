import time
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich import box
from rich.align import Align
from config import SUPERVISOR_MODEL

console = Console()

AGENT_COLORS = {
    "coder": "blue",
    "debugger": "magenta",
    "searcher": "cyan",
    "tester": "green",
    "spawn": "yellow",
}

MODEL_SHORT = SUPERVISOR_MODEL.split("/")[-1] if "/" in SUPERVISOR_MODEL else SUPERVISOR_MODEL


def print_welcome():
    logo = Text(
        r"""
+===============================================================+
|  _______   _______   ______   ______   __       __   ______   |
| |       \ |       \ |      \ /      \ |  \     /  \ /      \  |
| | $$$$$$$\| $$$$$$$\ \$$$$$$|  $$$$$$\| $$\   /  $$|  $$$$$$\ |
| | $$__/ $$| $$__| $$  | $$  | $$___\$$| $$$\ /  $$$| $$__| $$ |
| | $$    $$| $$    $$  | $$   \$$    \ | $$$$\  $$$$| $$    $$ |
| | $$$$$$$ | $$$$$$$\  | $$   _\$$$$$$\| $$\$$ $$ $$| $$$$$$$$ |
| | $$      | $$  | $$ _| $$_ |  \__| $$| $$ \$$$| $$| $$  | $$ |
| | $$      | $$  | $$|   $$ \ \$$    $$| $$  \$ | $$| $$  | $$ |
|  \$$       \$$   \$$ \$$$$$$  \$$$$$$  \$$      \$$ \$$   \$$ |
+===============================================================+""",
        style="bold cyan",
    )
    console.print()
    console.print(Align.center(logo))
    console.print()
    info = Table.grid(padding=(0, 1))
    info.add_column(style="dim", justify="right")
    info.add_column(style="white")
    info.add_row("agents", "coder  debugger  searcher  tester  spawn")
    info.add_row("model", MODEL_SHORT)
    panel = Panel(
        Align.center(info),
        border_style="cyan",
        box=box.HEAVY,
        padding=(1, 2),
    )
    console.print(panel)
    console.print()


def print_user_message(text: str):
    console.print()
    console.print(Text("You", style="bold yellow"))
    console.print(Text(text, style="yellow"))


def print_assistant_message(text: str, elapsed: float = 0):
    console.print()
    console.print(Text("Prisma", style="bold green"))
    md = Markdown(text)
    console.print(Panel(md, border_style="green", box=box.ROUNDED))
    if elapsed:
        status = Text(f"  {elapsed:.1f}s", style="dim")
        console.print(status)


def print_subtask_header(subtasks: list):
    console.print()
    console.print(Text("Prisma", style="bold green"))
    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim", width=2)
    table.add_column(style="bold")
    table.add_column(style="dim")
    for s in subtasks:
        agent_type = s["agent_type"]
        color = AGENT_COLORS.get(agent_type, "white")
        table.add_row(
            ">",
            Text(f"{agent_type}", style=color),
            Text(s["description"], style="dim"),
        )
    panel = Panel(
        table,
        title="sub-agents",
        title_align="left",
        border_style="blue",
        box=box.ROUNDED,
    )
    console.print(panel)


def print_subtask_completed(subtask: dict, result: str):
    agent_type = subtask["agent_type"]
    color = AGENT_COLORS.get(agent_type, "white")
    label = Text(f"  {agent_type}", style=color)
    panel = Panel(
        Markdown(result[:600] if result else "(no output)"),
        title=label,
        title_align="left",
        border_style=color,
        box=box.SQUARE,
        padding=(1, 2),
    )
    console.print(panel)


def print_error(text: str):
    console.print(f"[bold red]Error:[/bold red] {text}")


def print_exit():
    console.print()
    console.print("-" * 40, style="dim")
    console.print(Align.center(Text("bye", style="dim italic")))
    console.print()


def get_user_input():
    bar = Text("[+] ", style="cyan")
    bar.append("Prisma", style="bold")
    bar.append(Text(f" | {MODEL_SHORT}", style="dim"))
    console.print()
    console.print(bar)
    try:
        text = console.input("[bold yellow]You >[/bold yellow] ").strip()
        return text
    except (EOFError, KeyboardInterrupt):
        return ""
