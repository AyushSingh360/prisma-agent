"""
Prisma Display — Compatibility shim.

Preserves the original public API so existing tests and imports
continue to work. Delegates all rendering to the new UI modules.
"""

from rich.console import Console

from utils.theme import RICH_THEME, APP_NAME
from utils.renderers import (
    console,
    render_welcome,
    render_user_message,
    render_assistant_message,
    render_plan_card,
    render_tool_card,
    render_error,
    render_notification,
)
from utils.layout import PrismaLayout
from utils.input import (
    toggle_mode,
    get_mode,
    get_user_input as _get_user_input,
    set_pending_request,
    get_pending_request,
)

from config import SUPERVISOR_MODEL


# ──────────────────────────────────────────────────────────────
# Derived state (kept for backward compat)
# ──────────────────────────────────────────────────────────────

MODEL = SUPERVISOR_MODEL.split("/")[-1]

# Layout singleton — lazily initialized
_layout: PrismaLayout | None = None


def _get_layout() -> PrismaLayout:
    global _layout
    if _layout is None:
        _layout = PrismaLayout()
    return _layout


# ──────────────────────────────────────────────────────────────
# Public API (backward compat)
# ──────────────────────────────────────────────────────────────

def print_welcome():
    """Print the branded welcome splash."""
    layout = _get_layout()
    layout.initialize(MODEL)


def print_user_message(text):
    """Print a user message bubble."""
    console.print()
    console.print(render_user_message(text))


def print_assistant_message(text, elapsed=0):
    """Print an assistant response panel with Markdown."""
    console.print()
    console.print(render_assistant_message(text, elapsed))


def print_subtask_header(subtasks):
    """Print the plan card showing planned subtasks."""
    console.print()
    console.print(render_plan_card(subtasks))


def print_subtask_completed(subtask, result):
    """Print a completed subtask notification."""
    console.print(
        render_tool_card(
            name=subtask.get("description", "Task"),
            status=subtask.get("status", "completed"),
            agent_type=subtask.get("agent_type", ""),
        )
    )


def print_error(text):
    """Print an error panel."""
    console.print()
    console.print(render_error(text))


def print_prompt_chrome(mode: str, pending_request: str | None):
    """Print the pre-prompt status chrome."""
    layout = _get_layout()
    layout.print_prompt_chrome(mode, pending_request)


def get_user_input():
    """Get user input via the premium prompt."""
    return _get_user_input(console)


def print_exit():
    """Print exit message."""
    console.print()
    console.print(render_notification(f"{APP_NAME} session closed", "ok"))
    console.print()
