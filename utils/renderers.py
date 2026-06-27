"""
Prisma Renderers — Individual render functions for every UI element.

Each function returns a Rich renderable (Panel, Table, Text, Group, etc.)
that the layout engine or main loop can display.
"""

import os
import subprocess
from datetime import datetime

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text, Style
from rich.tree import Tree
from rich.align import Align
from rich.rule import Rule
from rich.columns import Columns
from rich import box

from utils.theme import (
    COLORS, STYLES, ICONS, AGENT_COLORS,
    APP_NAME, PANEL_BOX, SIDEBAR_WIDTH, RICH_THEME,
)


# ──────────────────────────────────────────────────────────────
# Console (singleton, themed)
# ──────────────────────────────────────────────────────────────

console = Console(theme=RICH_THEME, highlight=False)


# ──────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────

def _detect_git_branch() -> str:
    """Detect current git branch, return '—' if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "—"


def _detect_cwd() -> str:
    """Return a shortened version of the current working directory."""
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    if cwd.startswith(home):
        cwd = "~" + cwd[len(home):]
    # Shorten to last 2 components if long
    parts = cwd.replace("\\", "/").split("/")
    if len(parts) > 3:
        cwd = ".../" + "/".join(parts[-2:])
    return cwd


def render_header(model_name: str, is_online: bool = True) -> Panel:
    """Render the top header bar with agent name, model, status, cwd, branch."""
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=1)  # left
    grid.add_column(justify="center", ratio=2)  # center
    grid.add_column(justify="right", ratio=1)  # right

    # Left: Agent name
    left = Text()
    left.append(f" {ICONS['assistant']} ", style=STYLES["accent_bold"])
    left.append(APP_NAME, style=STYLES["header"])

    # Center: Model + status
    center = Text(justify="center")
    center.append(model_name, style=STYLES["header_model"])
    center.append("  ", style="default")
    if is_online:
        center.append(f"{ICONS['connected']} Online", style=STYLES["header_online"])
    else:
        center.append(f"{ICONS['disconnected']} Offline", style=STYLES["header_offline"])

    # Right: CWD + Branch
    branch = _detect_git_branch()
    cwd = _detect_cwd()
    right = Text(justify="right")
    right.append(cwd, style=STYLES["header_dim"])
    if branch != "—":
        right.append(f"  ⎇ {branch} ", style=STYLES["accent"])

    grid.add_row(left, center, right)

    return Panel(
        grid,
        border_style=STYLES["border_accent"],
        box=box.HEAVY_EDGE,
        padding=(0, 1),
        height=3,
    )


# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────

def render_sidebar(
    session_data: dict | None = None,
    is_online: bool = True,
) -> Panel:
    """Render the left status sidebar with SYSTEM and SESSION sections."""
    if session_data is None:
        session_data = {}

    lines = Text()

    # ── SYSTEM ──
    lines.append("━━━ SYSTEM ━━━\n", style=STYLES["sidebar_section"])
    lines.append("\n")

    api_status = "Online" if is_online else "Offline"
    api_icon = ICONS["connected"] if is_online else ICONS["disconnected"]
    api_style = STYLES["tool_success"] if is_online else STYLES["tool_error"]
    lines.append(f"  {api_icon} ", style=api_style)
    lines.append("API ", style=STYLES["sidebar_label"])
    lines.append(f"{api_status}\n", style=api_style)

    lines.append(f"  {ICONS['connected']} ", style=STYLES["tool_success"])
    lines.append("LSP ", style=STYLES["sidebar_label"])
    lines.append("Ready\n", style=STYLES["tool_success"])

    lines.append("\n")

    # ── SESSION ──
    lines.append("━━━ SESSION ━━━\n", style=STYLES["sidebar_section"])
    lines.append("\n")

    _sidebar_row(lines, "Turns",    str(session_data.get("turns", 0)))
    _sidebar_row(lines, "Messages", str(session_data.get("messages", 0)))
    _sidebar_row(lines, "Tokens",   _format_tokens(session_data.get("est_tokens", 0)))
    _sidebar_row(lines, "Elapsed",  session_data.get("elapsed", "0.0s"))

    lines.append("\n")

    # ── PROJECT ──
    lines.append("━━━ PROJECT ━━━\n", style=STYLES["sidebar_section"])
    lines.append("\n")

    _sidebar_row(lines, "Dir", _detect_cwd())
    _sidebar_row(lines, "Branch", _detect_git_branch())
    _sidebar_row(lines, "Mode", session_data.get("mode", "BUILD").upper())

    return Panel(
        lines,
        title=Text(f" {APP_NAME} ", style=STYLES["sidebar_title"]),
        border_style=STYLES["border"],
        box=PANEL_BOX,
        width=SIDEBAR_WIDTH,
        padding=(1, 1),
    )


def _sidebar_row(text: Text, label: str, value: str):
    """Append a label: value row to the sidebar text."""
    text.append(f"  {label:<9}", style=STYLES["sidebar_label"])
    text.append(f" {value}\n", style=STYLES["sidebar_value"])


def _format_tokens(n: int) -> str:
    """Format token count as human-readable."""
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


# ──────────────────────────────────────────────────────────────
# Messages
# ──────────────────────────────────────────────────────────────

def render_user_message(text: str) -> Panel:
    """Render a user message bubble."""
    content = Text(text, style=STYLES["user_msg"])
    return Panel(
        content,
        title=Text(f" {ICONS['user']} You ", style=STYLES["user_label"]),
        title_align="left",
        border_style=STYLES["border"],
        box=PANEL_BOX,
        padding=(0, 1),
    )


def render_assistant_message(text: str, elapsed: float = 0) -> Panel:
    """Render an assistant response with Markdown rendering."""
    body = Markdown(text)
    subtitle = None
    if elapsed > 0:
        subtitle = Text(f" {elapsed:.1f}s ", style=STYLES["dim"])

    return Panel(
        body,
        title=Text(f" {ICONS['assistant']} {APP_NAME} ", style=STYLES["assistant_label"]),
        title_align="left",
        subtitle=subtitle,
        subtitle_align="right",
        border_style=STYLES["border_accent"],
        box=PANEL_BOX,
        padding=(1, 2),
    )


def render_streaming_chunk(partial_text: str, show_cursor: bool = True) -> Panel:
    """Render a partial streaming response with optional blinking cursor."""
    body = Text()
    body.append(partial_text, style=STYLES["assistant_msg"])
    if show_cursor:
        body.append(ICONS["cursor"], style=STYLES["accent_bold"])

    return Panel(
        body,
        title=Text(f" {ICONS['assistant']} {APP_NAME} ", style=STYLES["assistant_label"]),
        title_align="left",
        border_style=STYLES["border_accent"],
        box=PANEL_BOX,
        padding=(1, 2),
    )


# ──────────────────────────────────────────────────────────────
# Tool Execution Cards
# ──────────────────────────────────────────────────────────────

def render_tool_card(
    name: str,
    status: str = "running",
    elapsed: float = 0,
    detail: str = "",
    agent_type: str = "",
) -> Text:
    """Render a compact tool execution status line."""
    line = Text()
    if status == "completed":
        line.append(f"  {ICONS['success']} ", style=STYLES["tool_success"])
    elif status == "failed":
        line.append(f"  {ICONS['error']} ", style=STYLES["tool_error"])
    else:
        line.append(f"  {ICONS['thinking']} ", style=STYLES["tool_running"])

    # Agent color
    color = AGENT_COLORS.get(agent_type, COLORS["text_secondary"])
    line.append(f"{name}", style=Style(color=color, bold=True))

    if elapsed > 0:
        line.append(f"  {elapsed:.1f}s", style=STYLES["dim"])

    if detail:
        line.append(f"  {ICONS['dot']} {detail}", style=STYLES["dim"])

    line.append("\n")
    return line


def render_tool_group(subtasks: list) -> Panel:
    """Render a group of tool execution cards."""
    content = Text()
    for s in subtasks:
        card = render_tool_card(
            name=s.get("description", "Task"),
            status=s.get("status", "pending"),
            agent_type=s.get("agent_type", ""),
        )
        content.append_text(card)

    return Panel(
        content,
        title=Text(f" {ICONS['arrow']} Execution ", style=STYLES["plan_header"]),
        title_align="left",
        border_style=STYLES["border"],
        box=PANEL_BOX,
        padding=(0, 1),
    )


# ──────────────────────────────────────────────────────────────
# Plan Card
# ──────────────────────────────────────────────────────────────

def render_plan_card(subtasks: list, elapsed: float = 0) -> Panel:
    """Render a structured plan with colored agent labels."""
    table = Table.grid(padding=(0, 1))
    table.add_column(width=10, style="bold")
    table.add_column(ratio=1)

    for s in subtasks:
        agent = s.get("agent_type", "spawn")
        color = AGENT_COLORS.get(agent, COLORS["text_secondary"])
        agent_text = Text(agent, style=Style(color=color, bold=True))
        desc_text = Text(s.get("description", ""), style=STYLES["dim"])
        table.add_row(agent_text, desc_text)

    subtitle = None
    if elapsed > 0:
        subtitle = Text(f" {elapsed:.1f}s ", style=STYLES["dim"])

    return Panel(
        table,
        title=Text(f" {ICONS['thinking']} Plan ", style=STYLES["plan_header"]),
        title_align="left",
        subtitle=subtitle,
        subtitle_align="right",
        border_style=STYLES["border"],
        box=PANEL_BOX,
        padding=(0, 1),
    )


# ──────────────────────────────────────────────────────────────
# Code Blocks
# ──────────────────────────────────────────────────────────────

def render_code_block(code: str, language: str = "python") -> Panel:
    """Render a syntax-highlighted code block with language label."""
    syntax = Syntax(
        code.strip(),
        language,
        theme="monokai",
        line_numbers=False,
        word_wrap=True,
        padding=(0, 1),
    )

    return Panel(
        syntax,
        title=Text(f" {language.upper()} ", style=STYLES["code_lang"]),
        title_align="left",
        border_style=STYLES["code_border"],
        box=PANEL_BOX,
        padding=(0, 0),
    )


# ──────────────────────────────────────────────────────────────
# File Tree
# ──────────────────────────────────────────────────────────────

def render_file_tree(files: list[dict]) -> Panel:
    """
    Render a file tree with status colors.
    files: list of {"path": str, "status": "added"|"modified"|"deleted"}
    """
    tree = Tree(
        Text("Modified Files", style=STYLES["accent_bold"]),
        guide_style=STYLES["border"],
    )

    status_styles = {
        "added":    STYLES["success"],
        "modified": STYLES["warning"],
        "deleted":  STYLES["error"],
    }
    status_icons = {
        "added":    ICONS["success"],
        "modified": ICONS["bullet"],
        "deleted":  ICONS["error"],
    }

    for f in files:
        status = f.get("status", "modified")
        style = status_styles.get(status, STYLES["dim"])
        icon = status_icons.get(status, ICONS["bullet"])
        label = Text()
        label.append(f"{icon} ", style=style)
        label.append(f["path"], style=style)
        tree.add(label)

    return Panel(
        tree,
        border_style=STYLES["border"],
        box=PANEL_BOX,
        padding=(0, 1),
    )


# ──────────────────────────────────────────────────────────────
# Progress Bar
# ──────────────────────────────────────────────────────────────

def render_progress(label: str, percentage: float) -> Text:
    """Render an inline progress bar: label ████████░░░░ 65%"""
    bar_width = 20
    filled = int(bar_width * percentage / 100)
    empty = bar_width - filled

    line = Text()
    line.append(f"  {label}  ", style=STYLES["progress_text"])
    line.append("█" * filled, style=STYLES["progress_bar"])
    line.append("░" * empty, style=STYLES["dim"])
    line.append(f" {percentage:.0f}%", style=STYLES["progress_text"])
    return line


# ──────────────────────────────────────────────────────────────
# Notifications
# ──────────────────────────────────────────────────────────────

def render_notification(message: str, level: str = "ok") -> Text:
    """Render a toast-style notification line."""
    line = Text()
    if level == "ok":
        line.append(f"  {ICONS['success']} ", style=STYLES["notification_ok"])
        line.append(message, style=STYLES["notification_ok"])
    elif level == "warn":
        line.append(f"  {ICONS['warning']} ", style=STYLES["notification_warn"])
        line.append(message, style=STYLES["notification_warn"])
    elif level == "error":
        line.append(f"  {ICONS['error']} ", style=STYLES["notification_err"])
        line.append(message, style=STYLES["notification_err"])
    else:
        line.append(f"  {ICONS['dot']} ", style=STYLES["dim"])
        line.append(message, style=STYLES["dim"])
    return line


# ──────────────────────────────────────────────────────────────
# Error
# ──────────────────────────────────────────────────────────────

def render_error(message: str) -> Panel:
    """Render an error panel."""
    content = Text()
    content.append(f" {ICONS['error']} ", style=STYLES["error"])
    content.append(message, style=STYLES["error_dim"])
    return Panel(
        content,
        title=Text(" Error ", style=STYLES["error"]),
        title_align="left",
        border_style=STYLES["error_dim"],
        box=PANEL_BOX,
        padding=(0, 1),
    )


# ──────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────

def render_footer(
    mode: str = "build",
    est_tokens: int = 0,
    model_name: str = "",
    latency: float = 0,
) -> Table:
    """Render the bottom footer bar with keybindings and stats."""
    grid = Table.grid(expand=True, padding=(0, 0))
    grid.add_column(ratio=3)
    grid.add_column(justify="right", ratio=2)

    # Left: keybindings
    keys = Text()
    _footer_key(keys, "Ctrl+C", "Exit")
    _footer_key(keys, "Ctrl+L", "Clear")
    _footer_key(keys, "Ctrl+J", "Newline")
    _footer_key(keys, "Tab", "Mode")
    _footer_key(keys, "Enter", "Send")

    # Right: stats
    stats = Text(justify="right")
    stats.append(f" {mode.upper()} ", style=STYLES["accent_bold"])
    if est_tokens > 0:
        stats.append(f" {ICONS['dot']} ", style=STYLES["dim"])
        stats.append(f"~{_format_tokens(est_tokens)} tokens", style=STYLES["dim"])
    if latency > 0:
        stats.append(f" {ICONS['dot']} ", style=STYLES["dim"])
        stats.append(f"{latency:.1f}s", style=STYLES["dim"])

    grid.add_row(keys, stats)
    return grid


def _footer_key(text: Text, key: str, desc: str):
    """Append a keybinding label to the footer."""
    text.append(f" {key} ", style=STYLES["footer_key"])
    text.append(f"{desc} ", style=STYLES["footer_desc"])


# ──────────────────────────────────────────────────────────────
# Welcome Screen
# ──────────────────────────────────────────────────────────────

def render_welcome(model_name: str = "") -> Panel:
    """Render the branded welcome splash screen."""
    ascii_art = Text(justify="center")
    art_lines = [
        "    ____  ____  _________ __  ___ ___",
        "   / __ \\/ __ \\/  _/ ___//  |/  //   |",
        "  / /_/ / /_/ // / \\__ \\/ /|_/ // /| |",
        " / ____/ _, _// / ___/ / /  / // ___ |",
        "/_/   /_/ |_/___//____/_/  /_//_/  |_|",
    ]
    for line in art_lines:
        ascii_art.append(line + "\n", style=STYLES["accent"])

    subtitle = Text(justify="center")
    subtitle.append("\n")
    subtitle.append("Multi-Agent Coding Assistant", style=STYLES["dim"])
    subtitle.append("\n\n")
    if model_name:
        subtitle.append(f"Model: {model_name}", style=STYLES["header_model"])
        subtitle.append("\n")
    subtitle.append("Type your request below. ", style=STYLES["dim"])
    subtitle.append("Use /help for commands.", style=STYLES["dim"])
    subtitle.append("\n")

    body = Group(ascii_art, subtitle)

    return Panel(
        Align.center(body),
        border_style=STYLES["border_accent"],
        box=PANEL_BOX,
        padding=(1, 2),
    )


# ──────────────────────────────────────────────────────────────
# Thinking / Status Line
# ──────────────────────────────────────────────────────────────

def render_thinking(frame: str, status_text: str = "Thinking...") -> Text:
    """Render a spinner frame + status text for the status bar."""
    line = Text()
    line.append(f" {frame} ", style=STYLES["spinner"])
    line.append(status_text, style=STYLES["spinner_text"])
    return line


def render_status_idle() -> Text:
    """Render idle status (empty)."""
    return Text(" ", style=STYLES["dim"])
