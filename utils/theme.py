"""
Prisma Theme — Centralized design token registry.

All colors, styles, icons, and visual constants for the terminal UI.
Light-blue primary accent with a dark background palette.
"""

from rich.style import Style
from rich.theme import Theme
from rich import box


# ──────────────────────────────────────────────────────────────
# Color Palette
# ──────────────────────────────────────────────────────────────

COLORS = {
    # Primary accent
    "primary":       "#6EC6FF",
    "primary_dim":   "#3A8FCC",
    "primary_bright":"#A0DCFF",

    # Semantic
    "success":       "#10B981",
    "warning":       "#F59E0B",
    "error":         "#EF4444",
    "info":          "#8B5CF6",

    # Surfaces
    "surface":       "#0B1220",
    "surface_alt":   "#111827",
    "surface_hover": "#1F2937",

    # Text
    "text":          "#E5E7EB",
    "text_secondary":"#9CA3AF",
    "text_muted":    "#6B7280",

    # Borders
    "border":        "#1E3A5F",
    "border_dim":    "#1A2332",

    # Agent colors
    "agent_coder":   "#3B82F6",
    "agent_debugger":"#A855F7",
    "agent_searcher":"#06B6D4",
    "agent_tester":  "#10B981",
    "agent_spawner": "#F59E0B",
}

AGENT_COLORS = {
    "coder":    COLORS["agent_coder"],
    "debugger": COLORS["agent_debugger"],
    "searcher": COLORS["agent_searcher"],
    "tester":   COLORS["agent_tester"],
    "spawn":    COLORS["agent_spawner"],
    "spawner":  COLORS["agent_spawner"],
}


# ──────────────────────────────────────────────────────────────
# Rich Styles
# ──────────────────────────────────────────────────────────────

STYLES = {
    "header":          Style(color=COLORS["primary"], bold=True),
    "header_dim":      Style(color=COLORS["text_muted"]),
    "header_model":    Style(color=COLORS["text_secondary"]),
    "header_online":   Style(color=COLORS["success"], bold=True),
    "header_offline":  Style(color=COLORS["error"], bold=True),

    "sidebar_title":   Style(color=COLORS["primary"], bold=True),
    "sidebar_label":   Style(color=COLORS["text_muted"]),
    "sidebar_value":   Style(color=COLORS["text_secondary"]),
    "sidebar_section": Style(color=COLORS["primary_dim"], bold=True),

    "user_label":      Style(color=COLORS["primary"], bold=True),
    "user_msg":        Style(color=COLORS["text"]),

    "assistant_label": Style(color=COLORS["primary_bright"], bold=True),
    "assistant_msg":   Style(color=COLORS["text"]),

    "tool_running":    Style(color=COLORS["primary_dim"]),
    "tool_success":    Style(color=COLORS["success"]),
    "tool_error":      Style(color=COLORS["error"]),
    "tool_name":       Style(color=COLORS["text_secondary"], bold=True),

    "dim":             Style(color=COLORS["text_muted"]),
    "accent":          Style(color=COLORS["primary"]),
    "accent_bold":     Style(color=COLORS["primary"], bold=True),
    "muted":           Style(color=COLORS["text_muted"], dim=True),
    "success":         Style(color=COLORS["success"]),
    "warning":         Style(color=COLORS["warning"]),
    "error":           Style(color=COLORS["error"], bold=True),
    "error_dim":       Style(color=COLORS["error"]),

    "border":          Style(color=COLORS["border"]),
    "border_accent":   Style(color=COLORS["primary_dim"]),

    "footer_key":      Style(color=COLORS["primary"], bold=True),
    "footer_desc":     Style(color=COLORS["text_muted"]),

    "code_border":     Style(color=COLORS["border"]),
    "code_lang":       Style(color=COLORS["primary_dim"], bold=True),

    "plan_header":     Style(color=COLORS["primary"], bold=True),

    "notification_ok": Style(color=COLORS["success"]),
    "notification_warn": Style(color=COLORS["warning"]),
    "notification_err":  Style(color=COLORS["error"]),

    "spinner":         Style(color=COLORS["primary"]),
    "spinner_text":    Style(color=COLORS["text_muted"]),

    "progress_bar":    Style(color=COLORS["primary"]),
    "progress_text":   Style(color=COLORS["text_muted"]),
}


# ──────────────────────────────────────────────────────────────
# Icons & Glyphs
# ──────────────────────────────────────────────────────────────

ICONS = {
    "success":    "✓",
    "error":      "✗",
    "warning":    "⚠",
    "bullet":     "●",
    "bullet_dim": "○",
    "arrow":      "▸",
    "arrow_down": "▾",
    "cursor":     "▋",
    "dot":        "·",
    "dash":       "─",
    "bar":        "│",
    "corner_tl":  "┌",
    "corner_tr":  "┐",
    "corner_bl":  "└",
    "corner_br":  "┘",
    "tee_r":      "├",
    "tee_l":      "┤",
    "cross":      "┼",
    "ellipsis":   "…",
    "user":       "▸",
    "assistant":  "◆",
    "thinking":   "◇",
    "connected":  "●",
    "disconnected":"○",
}


# ──────────────────────────────────────────────────────────────
# Spinner Animation Frames
# ──────────────────────────────────────────────────────────────

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

THINKING_STATUSES = [
    "Thinking...",
    "Searching project...",
    "Reading files...",
    "Calling tool...",
    "Editing code...",
    "Generating response...",
    "Applying changes...",
]


# ──────────────────────────────────────────────────────────────
# Box Styles
# ──────────────────────────────────────────────────────────────

# Thin rounded box for panels
PANEL_BOX = box.ROUNDED
# Minimal box for tables
TABLE_BOX = box.SIMPLE_HEAVY
# No border for inline layouts
MINIMAL_BOX = box.SIMPLE


# ──────────────────────────────────────────────────────────────
# Rich Theme (for Console)
# ──────────────────────────────────────────────────────────────

RICH_THEME = Theme({
    "prisma.primary":     COLORS["primary"],
    "prisma.dim":         COLORS["text_muted"],
    "prisma.success":     COLORS["success"],
    "prisma.warning":     COLORS["warning"],
    "prisma.error":       COLORS["error"],
    "prisma.text":        COLORS["text"],
    "prisma.muted":       COLORS["text_muted"],
    "prisma.border":      COLORS["border"],
    "prisma.accent":      COLORS["primary"],
})


# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

APP_NAME = "Prisma"
SIDEBAR_WIDTH = 28
HEADER_HEIGHT = 3
FOOTER_HEIGHT = 1
STATUS_HEIGHT = 1
REFRESH_RATE = 10          # FPS for Live refresh
CURSOR_BLINK_MS = 500     # ms between cursor blink toggles
