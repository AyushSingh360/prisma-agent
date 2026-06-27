"""
Prisma Input — Premium multi-line Prompt Toolkit input session.

Provides keybindings, command completion, history, and placeholder text.
"""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import HTML, ANSI
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import has_completions
from prompt_toolkit.styles import Style as PTStyle

from utils.theme import COLORS, APP_NAME
from utils.commands import CommandCompleter


# ──────────────────────────────────────────────────────────────
# Prompt Toolkit Style (matches Prisma theme)
# ──────────────────────────────────────────────────────────────

PT_STYLE = PTStyle.from_dict({
    "prompt":       f"{COLORS['primary']} bold",
    "prompt.mode":  f"{COLORS['text_muted']}",
    "":             f"{COLORS['text']}",       # default input text
    "placeholder":  f"{COLORS['text_muted']} italic",
    "bottom-toolbar": f"bg:{COLORS['surface_alt']} {COLORS['text_muted']}",
})


# ──────────────────────────────────────────────────────────────
# State
# ──────────────────────────────────────────────────────────────

MODE = "build"
_pending_request = None
_history = InMemoryHistory()
_session = None


def toggle_mode():
    """Toggle between build and plan modes."""
    global MODE
    MODE = "plan" if MODE == "build" else "build"


def get_mode():
    """Return the current mode."""
    return MODE


def set_pending_request(text: str | None):
    """Set a pending request to be executed when switching to build mode."""
    global _pending_request
    _pending_request = text


def get_pending_request():
    """Get the current pending request."""
    return _pending_request


# ──────────────────────────────────────────────────────────────
# Keybindings
# ──────────────────────────────────────────────────────────────

def _build_keybindings(console_ref):
    """Build the prompt_toolkit keybindings."""
    bindings = KeyBindings()

    @bindings.add("tab", filter=~has_completions)
    def _toggle_mode(event):
        """Toggle between build/plan modes on Tab."""
        global MODE, _pending_request
        toggle_mode()
        if console_ref:
            console_ref.print(f"\n  Switched to [bold]{MODE.upper()}[/bold] mode\n")
        if MODE == "build" and _pending_request:
            event.app.exit(result="__EXECUTE_PENDING__")
            return
        event.app.invalidate()

    @bindings.add("c-l")
    def _clear_screen(event):
        """Clear the screen."""
        event.app.renderer.clear()

    @bindings.add("c-j")
    def _newline(event):
        """Insert a newline (multi-line editing)."""
        event.current_buffer.insert_text("\n")

    return bindings


# ──────────────────────────────────────────────────────────────
# Prompt Session
# ──────────────────────────────────────────────────────────────

def _get_session(console_ref=None):
    """Get or create the PromptSession singleton."""
    global _session
    if _session is None:
        _session = PromptSession(
            history=_history,
            completer=CommandCompleter(),
            complete_while_typing=True,
            key_bindings=_build_keybindings(console_ref),
            style=PT_STYLE,
            placeholder=HTML(
                f'<style fg="{COLORS["text_muted"]}" italic="true">  Ask anything...</style>'
            ),
            multiline=False,  # Enter sends; Ctrl+J for newline
        )
    return _session


def get_user_input(console_ref=None):
    """
    Show the prompt and get user input.

    Returns:
        tuple: (user_text, current_mode)
    """
    try:
        prompt_text = HTML(
            f'<style fg="{COLORS["primary"]}" bold="true">{APP_NAME.lower()}</style>'
            f'<style fg="{COLORS["text_muted"]}"> [{MODE}]</style>'
            f'<style fg="{COLORS["primary"]}"> ❯ </style>'
        )

        text = _get_session(console_ref).prompt(prompt_text).strip()
        return text, MODE
    except (EOFError, KeyboardInterrupt):
        return "", MODE
