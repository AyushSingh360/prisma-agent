"""
Prisma Layout — Full-screen terminal layout engine.

Manages the header, sidebar, main chat area, status bar, and footer
using Rich's Layout system.
"""

import time
from typing import Optional

from rich.console import Console, Group, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box

from utils.theme import (
    COLORS, STYLES, ICONS, APP_NAME,
    SIDEBAR_WIDTH, HEADER_HEIGHT, PANEL_BOX, RICH_THEME,
)
from utils.renderers import (
    console,
    render_header,
    render_sidebar,
    render_footer,
    render_welcome,
    render_thinking,
    render_status_idle,
    render_notification,
)


# ──────────────────────────────────────────────────────────────
# Prisma Layout Manager
# ──────────────────────────────────────────────────────────────

class PrismaLayout:
    """
    Manages the full-screen terminal layout.

    The layout is NOT a persistent full-screen application — instead it
    prints structured panels to the console in sequence, maintaining
    the premium aesthetic while staying compatible with prompt_toolkit's
    input handling.
    """

    def __init__(self):
        self._console = console
        self._model_name = ""
        self._is_online = True
        self._session_data = {
            "turns": 0,
            "messages": 0,
            "est_tokens": 0,
            "elapsed": "0.0s",
            "mode": "BUILD",
        }
        self._start_time = time.time()
        self._last_latency = 0.0
        self._notifications: list[tuple[str, str]] = []

    @property
    def console(self) -> Console:
        return self._console

    def initialize(self, model_name: str):
        """Initialize the layout with model info and print the welcome screen."""
        self._model_name = model_name
        self._is_online = True
        self._console.clear()
        self._console.print(render_welcome(model_name))
        self._console.print()

    def print_header(self):
        """Print the header bar."""
        self._console.print(render_header(self._model_name, self._is_online))

    def print_sidebar_snapshot(self):
        """Print a compact sidebar-style status block."""
        sidebar = render_sidebar(self._session_data, self._is_online)
        self._console.print(sidebar)

    def print_footer(self):
        """Print the footer keybinding bar."""
        footer = render_footer(
            mode=self._session_data.get("mode", "BUILD"),
            est_tokens=self._session_data.get("est_tokens", 0),
            model_name=self._model_name,
            latency=self._last_latency,
        )
        self._console.print(footer)
        self._console.print()

    def print_prompt_chrome(self, mode: str, pending_request: str | None):
        """Print the pre-prompt status bar (mode + queue status)."""
        self._session_data["mode"] = mode.upper()
        elapsed = time.time() - self._start_time
        self._session_data["elapsed"] = f"{elapsed:.0f}s"

        # Compact status line
        status = Text()
        status.append(f" {ICONS['assistant']} ", style=STYLES["accent_bold"])
        status.append(APP_NAME, style=STYLES["accent_bold"])
        status.append(f" {ICONS['dot']} ", style=STYLES["dim"])
        status.append(self._model_name, style=STYLES["header_model"])
        status.append(f" {ICONS['dot']} ", style=STYLES["dim"])
        status.append(mode.upper(), style=STYLES["accent"])

        if pending_request:
            status.append(f" {ICONS['dot']} ", style=STYLES["dim"])
            status.append("queued", style=STYLES["warning"])

        # Right side: tokens + turns
        turns = self._session_data.get("turns", 0)
        tokens = self._session_data.get("est_tokens", 0)
        right_info = Text(justify="right")
        if tokens > 0:
            right_info.append(f"~{_fmt_tokens(tokens)} tokens", style=STYLES["dim"])
            right_info.append(f" {ICONS['dot']} ", style=STYLES["dim"])
        right_info.append(f"Turn {turns}", style=STYLES["dim"])
        if self._last_latency > 0:
            right_info.append(f" {ICONS['dot']} ", style=STYLES["dim"])
            right_info.append(f"{self._last_latency:.1f}s", style=STYLES["dim"])

        from rich.table import Table
        grid = Table.grid(expand=True)
        grid.add_column(ratio=3)
        grid.add_column(justify="right", ratio=2)
        grid.add_row(status, right_info)

        self._console.print(
            Panel(
                grid,
                border_style=STYLES["border"],
                box=box.SQUARE,
                padding=(0, 1),
                height=3,
            )
        )

        # Print any pending notifications
        for msg, level in self._notifications:
            self._console.print(render_notification(msg, level))
        self._notifications.clear()

    def update_session(
        self,
        turns: int | None = None,
        messages: int | None = None,
        est_tokens: int | None = None,
        mode: str | None = None,
        latency: float | None = None,
    ):
        """Update session tracking data."""
        if turns is not None:
            self._session_data["turns"] = turns
        if messages is not None:
            self._session_data["messages"] = messages
        if est_tokens is not None:
            self._session_data["est_tokens"] = est_tokens
        if mode is not None:
            self._session_data["mode"] = mode.upper()
        if latency is not None:
            self._last_latency = latency
        elapsed = time.time() - self._start_time
        self._session_data["elapsed"] = f"{elapsed:.0f}s"

    def add_notification(self, message: str, level: str = "ok"):
        """Queue a notification to be shown before the next prompt."""
        self._notifications.append((message, level))

    def set_online(self, is_online: bool):
        """Update the API connection status."""
        self._is_online = is_online


def _fmt_tokens(n: int) -> str:
    """Format token count."""
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)
