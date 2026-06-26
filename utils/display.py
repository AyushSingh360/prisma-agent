from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import completion_is_selected, has_completions
from config import SUPERVISOR_MODEL
from utils.commands import CommandCompleter

console = Console()

AGENT_COLORS = {
    "coder": "blue",
    "debugger": "magenta",
    "searcher": "cyan",
    "tester": "green",
    "spawn": "yellow",
}

MODEL_SHORT = SUPERVISOR_MODEL.split("/")[-1] if "/" in SUPERVISOR_MODEL else SUPERVISOR_MODEL

_mode = "build"
_session = None
_pending_request = None


def toggle_mode():
    global _mode
    _mode = "plan" if _mode == "build" else "build"
    return _mode


def get_mode():
    return _mode


def set_pending_request(text: str | None):
    global _pending_request
    _pending_request = text


def get_pending_request():
    return _pending_request


def _build_kb():
    kb = KeyBindings()

    @kb.add("tab", filter=~has_completions)
    def _(event):
        previous_mode = _mode
        toggle_mode()
        mode_label = _mode.upper()
        console.print()
        console.print(Text(f"Switched to {mode_label} mode", style="dim"))
        if previous_mode == "plan" and _mode == "build" and _pending_request:
            event.app.exit(result="__EXECUTE_PENDING__")
            return
        event.app.invalidate()

    return kb


def _get_session():
    global _session
    if _session is None:
        _session = PromptSession(
            history=InMemoryHistory(),
            completer=CommandCompleter(),
            complete_while_typing=True,
            key_bindings=_build_kb(),
        )
    return _session


def print_welcome():
    console.print()
    console.print(Text("prisma", style="bold"))
    console.print(Text(f"model: {MODEL_SHORT}  |  /help for commands", style="dim"))
    console.print()


def print_user_message(text: str):
    console.print()
    console.print(Text(text))


def print_assistant_message(text: str, elapsed: float = 0):
    console.print()
    md = Markdown(text)
    console.print(md)


def print_subtask_header(subtasks: list):
    console.print()
    for s in subtasks:
        agent_type = s["agent_type"]
        color = AGENT_COLORS.get(agent_type, "white")
        console.print(Text(f"  {agent_type}", style=color), end="")
        console.print(Text(f" {s['description']}", style="dim"))


def print_subtask_completed(subtask: dict, result: str):
    agent_type = subtask["agent_type"]
    color = AGENT_COLORS.get(agent_type, "white")
    console.print()
    console.print(Text(f"  {agent_type}", style=color), end="")
    console.print(Text(" done", style="dim"))
    if result:
        console.print()
        for line in result.split("\n")[:8]:
            console.print(Text(f"    {line}", style="dim"))


def print_error(text: str):
    console.print()
    console.print(Text(f"error: {text}", style="red"))


def print_exit():
    console.print()


def get_user_input():
    mode_label = _mode.upper()
    try:
        try:
            session = _get_session()
            prompt_html = "<dim>></dim> " if _mode == "build" else "<dim>(plan)></dim> "
            text = session.prompt(HTML(prompt_html)).strip()
        except Exception:
            text = input("> ").strip()
        return text, _mode
    except (EOFError, KeyboardInterrupt):
        return "", _mode
