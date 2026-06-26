from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import has_completions
from config import SUPERVISOR_MODEL
from utils.commands import CommandCompleter

console = Console()

APP_NAME = "Prisma"
MODEL = SUPERVISOR_MODEL.split("/")[-1]

MODE = "build"

history = InMemoryHistory()

session = None
_pending_request = None


def toggle_mode():
    global MODE
    MODE = "plan" if MODE == "build" else "build"


def get_mode():
    return MODE


def kb():

    bindings = KeyBindings()

    @bindings.add("tab", filter=~has_completions)
    def _(event):
        global MODE, _pending_request
        toggle_mode()
        console.print(f"\nSwitched to {MODE.upper()} mode\n")
        if MODE == "build" and _pending_request:
            event.app.exit(result="__EXECUTE_PENDING__")
            return
        event.app.invalidate()

    return bindings


def get_session():
    global session

    if session is None:

        session = PromptSession(
            history=history,
            completer=CommandCompleter(),
            complete_while_typing=True,
            key_bindings=kb(),
        )

    return session


def set_pending_request(text: str | None):
    global _pending_request
    _pending_request = text


def get_pending_request():
    return _pending_request


def print_welcome():
    console.print()
    title = Text(APP_NAME, style="bold cyan")
    subtitle = Text("Claude-style CLI for your AI agent", style="dim")
    header = Group(
        title,
        subtitle,
        Text(f"model: {MODEL}", style="dim"),
    )
    console.print(Panel(header, border_style="cyan", box=box.ROUNDED, padding=(1, 2)))
    console.print()


def print_user_message(text):
    console.print()
    console.print(
        Panel(
            Text(text),
            title="You",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def print_assistant_message(text, elapsed=0):
    console.print()
    body = Markdown(text)
    subtitle = f"{elapsed:.1f}s" if elapsed else None
    console.print(
        Panel(
            body,
            title=APP_NAME,
            subtitle=subtitle,
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def print_subtask_header(subtasks):
    console.print()
    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column(style="white")
    for s in subtasks:
        color = {"coder": "blue", "debugger": "magenta", "searcher": "cyan", "tester": "green"}.get(s["agent_type"], "white")
        table.add_row(Text(s["agent_type"], style=color), s["description"])
    console.print(
        Panel(
            table,
            title="Plan",
            border_style="dim cyan",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def print_subtask_completed(subtask, result):
    console.print()
    console.print(
        Text(
            f"{subtask['agent_type']} done",
            style="green",
        )
    )


def print_error(text):
    console.print()
    console.print(
        Panel(
            Text(text, style="red"),
            title="Error",
            border_style="red",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def print_prompt_chrome(mode: str, pending_request: str | None):
    pending = "queued" if pending_request else "idle"
    status = Table.grid(expand=True)
    status.add_column(ratio=2)
    status.add_column(justify="right")
    status.add_row(
        Text(f"{APP_NAME}", style="bold cyan"),
        Text(f"{mode.upper()} | {pending} | {MODEL}", style="dim"),
    )
    console.print(Panel(status, border_style="dim", box=box.SQUARE, padding=(0, 1)))


def get_user_input():
    try:
        prompt = f"<ansicyan>{APP_NAME.lower()}</ansicyan> <ansidim>[{MODE}]</ansidim> > "

        text = get_session().prompt(HTML(prompt)).strip()
        return text, MODE
    except (EOFError, KeyboardInterrupt):
        return "", MODE


def print_exit():
    console.print()
    console.print(Text(f"{APP_NAME} session closed", style="dim"))
